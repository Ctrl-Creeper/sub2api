//go:build unit

package service

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/Wei-Shaw/sub2api/internal/pkg/claude"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/require"
)

func outboundIdentityTestAccount(id int64, identity string) *Account {
	extra := map[string]any{}
	if identity != "" {
		extra["outbound_identity"] = identity
	}
	return &Account{
		ID:          id,
		Name:        "outbound-identity-test",
		Platform:    PlatformAnthropic,
		Type:        AccountTypeAPIKey,
		Status:      StatusActive,
		Concurrency: 1,
		Credentials: map[string]any{
			"api_key":  "sk-ant-outbound",
			"base_url": "http://testserver.example",
		},
		Extra: extra,
	}
}

func claudeCodeStyleClientHeaders() http.Header {
	h := http.Header{}
	h.Set("User-Agent", "claude-cli/2.1.258 (external, cli)")
	h.Set("X-App", "cli")
	h.Set("X-Stainless-Lang", "js")
	h.Set("X-Stainless-Runtime", "node")
	h.Set("X-Stainless-Runtime-Version", "v24.3.0")
	h.Set("X-Claude-Code-Session-Id", "sess-123")
	h.Set("X-Client-Request-Id", "req-456")
	h.Set("Anthropic-Dangerous-Direct-Browser-Access", "true")
	h.Set("anthropic-beta", "claude-code-20250219,oauth-2025-04-20")
	h.Set("anthropic-version", "2023-06-01")
	return h
}

// GetOutboundIdentity 的平台/类型/取值校验。
func TestGetOutboundIdentity(t *testing.T) {
	require.Equal(t, OutboundIdentityClient, outboundIdentityTestAccount(1, "").GetOutboundIdentity())
	require.Equal(t, OutboundIdentityClient, outboundIdentityTestAccount(1, "nonsense").GetOutboundIdentity())
	require.Equal(t, OutboundIdentityHermes, outboundIdentityTestAccount(1, "hermes_agent").GetOutboundIdentity())
	require.Equal(t, OutboundIdentityPlain, outboundIdentityTestAccount(1, "plain").GetOutboundIdentity())

	oauth := outboundIdentityTestAccount(1, "hermes_agent")
	oauth.Type = AccountTypeOAuth
	require.Equal(t, OutboundIdentityClient, oauth.GetOutboundIdentity(), "OAuth 账号不受出站身份影响")

	openai := outboundIdentityTestAccount(1, "hermes_agent")
	openai.Platform = PlatformOpenAI
	require.Equal(t, OutboundIdentityClient, openai.GetOutboundIdentity(), "非 Anthropic 平台不受影响")
}

// hermes_agent：header 整组替换为 Anthropic Python SDK 指纹，CC 特征头剥净。
func TestApplyOutboundIdentityHeaders_Hermes(t *testing.T) {
	h := claudeCodeStyleClientHeaders()
	applyAnthropicOutboundIdentityHeaders(OutboundIdentityHermes, h)

	require.Equal(t, "Anthropic/Python "+claude.HermesPinnedAnthropicSDKVersion, getHeaderRaw(h, "User-Agent"))
	require.Equal(t, "python", getHeaderRaw(h, "X-Stainless-Lang"))
	require.Equal(t, "CPython", getHeaderRaw(h, "X-Stainless-Runtime"))
	require.Equal(t, claude.HermesPythonVersion, getHeaderRaw(h, "X-Stainless-Runtime-Version"))
	require.Equal(t, "false", getHeaderRaw(h, "X-Stainless-Async"))
	require.Equal(t, claude.HermesBetaHeader, getHeaderRaw(h, "anthropic-beta"))
	require.NotContains(t, claude.HermesBetaHeader, "claude-code-20250219")

	// CC 特征头必须剥净。
	require.Empty(t, getHeaderRaw(h, "X-App"))
	require.Empty(t, getHeaderRaw(h, "X-Claude-Code-Session-Id"))
	require.Empty(t, getHeaderRaw(h, "X-Client-Request-Id"))
	require.Empty(t, getHeaderRaw(h, "Anthropic-Dangerous-Direct-Browser-Access"))
}

// plain：CC 特征与 js 指纹头剥净，beta 删除，UA 显式。
func TestApplyOutboundIdentityHeaders_Plain(t *testing.T) {
	h := claudeCodeStyleClientHeaders()
	applyAnthropicOutboundIdentityHeaders(OutboundIdentityPlain, h)

	require.Empty(t, getHeaderRaw(h, "X-App"))
	require.Empty(t, getHeaderRaw(h, "X-Stainless-Lang"))
	require.Empty(t, getHeaderRaw(h, "X-Stainless-Runtime"))
	require.Empty(t, getHeaderRaw(h, "anthropic-beta"))
	require.Empty(t, getHeaderRaw(h, "X-Claude-Code-Session-Id"))
	require.NotEmpty(t, getHeaderRaw(h, "User-Agent"))
}

// client（缺省）：no-op，不改变任何头。
func TestApplyOutboundIdentityHeaders_ClientNoop(t *testing.T) {
	h := claudeCodeStyleClientHeaders()
	before := map[string][]string{}
	for k, v := range h {
		before[k] = v
	}
	applyAnthropicOutboundIdentityHeaders(OutboundIdentityClient, h)
	require.Equal(t, before, map[string][]string(h))
}

// body 层：hermes/plain 剥 metadata；client no-op。
func TestApplyOutboundIdentityBody(t *testing.T) {
	body := []byte(`{"model":"claude-sonnet-4-5","metadata":{"user_id":"user_abc"},"messages":[{"role":"user","content":"hi"}]}`)

	hermesBody := applyAnthropicOutboundIdentityBody(OutboundIdentityHermes, bytes.Clone(body))
	assertStrippedMetadata(t, hermesBody)

	plainBody := applyAnthropicOutboundIdentityBody(OutboundIdentityPlain, bytes.Clone(body))
	assertStrippedMetadata(t, plainBody)

	clientBody := applyAnthropicOutboundIdentityBody(OutboundIdentityClient, bytes.Clone(body))
	require.Contains(t, string(clientBody), `"user_id"`, "client 身份不得改写 body")
}

func assertStrippedMetadata(t *testing.T, body []byte) {
	t.Helper()
	var m map[string]any
	require.NoError(t, json.Unmarshal(body, &m))
	require.NotContains(t, m, "metadata")
	require.Contains(t, m, "messages")
}

// 端到端：buildUpstreamRequestAnthropicAPIKeyPassthrough 在 hermes 身份下的最终头。
func TestAnthropicPassthroughBuild_HermesIdentity(t *testing.T) {
	gin.SetMode(gin.TestMode)

	rec := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(rec)
	c.Request = httptest.NewRequest(http.MethodPost, "/v1/messages", nil)
	for k, v := range map[string]string{
		"User-Agent": "claude-cli/2.1.258 (external, cli)",
		"X-App":      "cli",
		"anthropic-beta": "claude-code-20250219,oauth-2025-04-20",
	} {
		c.Request.Header.Set(k, v)
	}

	cfg := rawChatCompletionsTestConfig()
	svc := &GatewayService{
		cfg:                  cfg,
		responseHeaderFilter: compileResponseHeaderFilter(cfg),
	}

	account := outboundIdentityTestAccount(9, "hermes_agent")

	body := []byte(`{"model":"claude-sonnet-4-5-20250929","metadata":{"user_id":"user_abc"},"messages":[{"role":"user","content":[{"type":"text","text":"hi"}]}],"max_tokens":16}`)

	req, wire, err := svc.buildUpstreamRequestAnthropicAPIKeyPassthrough(c.Request.Context(), c, account, body, "sk-key")
	require.NoError(t, err)

	require.Equal(t, "Anthropic/Python "+claude.HermesPinnedAnthropicSDKVersion, getHeaderRaw(req.Header, "User-Agent"))
	require.Equal(t, claude.HermesBetaHeader, getHeaderRaw(req.Header, "anthropic-beta"))
	require.Empty(t, getHeaderRaw(req.Header, "X-App"))
	require.Empty(t, getHeaderRaw(req.Header, "X-Claude-Code-Session-Id"))
	assertStrippedMetadata(t, wire)
	// 认证头保持账号语义。
	require.Equal(t, "sk-key", getHeaderRaw(req.Header, "X-Api-Key"))
}
