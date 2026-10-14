package service

import (
	"bytes"
	"net/http"

	"github.com/Wei-Shaw/sub2api/internal/pkg/claude"
	"github.com/tidwall/sjson"
)

// claudeOutboundIdentity* 与 Account.GetOutboundIdentity 的常量一一对应。
const (
	claudeOutboundIdentityHermes = "hermes_agent"
	claudeOutboundIdentityPlain  = "plain"
)

// claudeClientOnlyHeaderNames 是 Claude Code（js 客户端）特有、Python SDK
// 客户端不会发送的请求头。出站身份改写时从请求头集合中整组剥离。
var claudeClientOnlyHeaderNames = []string{
	"X-App",
	"X-Claude-Code-Session-Id",
	"X-Client-Request-Id",
	"Anthropic-Dangerous-Direct-Browser-Access",
}

// applyAnthropicOutboundIdentityBody 执行出站身份的 body 层改写：
// hermes_agent / plain 均剥掉 metadata（API-key JSON 客户端不带
// metadata.user_id；该字段是 Claude Code 的强身份信号）。
// 调用时机：早于 finalBeta 计算与 body sanitize（剥完的 body 才参与
// beta 对称净化与 CCH 签名）。
func applyAnthropicOutboundIdentityBody(identity string, body []byte) []byte {
	switch identity {
	case claudeOutboundIdentityHermes, claudeOutboundIdentityPlain:
		if bytes.Contains(body, []byte(`"metadata"`)) {
			if next, err := sjson.DeleteBytes(body, "metadata"); err == nil {
				body = next
			}
		}
		return body
	default:
		return body
	}
}

// applyAnthropicOutboundIdentityHeaders 执行出站身份的 header 层改写。
// 注入点契约：在白名单透传与认证头之后、账号级 HeaderOverrides 与
// filterSonnet55ToolsetBetaHeader 之前调用——覆写保留最终决定权。
func applyAnthropicOutboundIdentityHeaders(identity string, h http.Header) {
	switch identity {
	case claudeOutboundIdentityHermes:
		// 剥离 Claude Code 客户端特征头（含白名单透传进来的残留）。
		for _, k := range claudeClientOnlyHeaderNames {
			deleteHeaderAllForms(h, k)
		}
		// 强制覆盖为 Hermes（Anthropic Python SDK）指纹头。
		for k, v := range claude.HermesHeaders() {
			setHeaderRaw(h, k, v)
		}
	case claudeOutboundIdentityPlain:
		// 朴素身份：剥离 CC 特征头与 js 客户端指纹头，不注入替代指纹。
		// User-Agent 显式设置以避免 Go 默认补 Go-http-client/1.1。
		for _, k := range append(append([]string(nil), claudeClientOnlyHeaderNames...),
			"X-Stainless-Lang",
			"X-Stainless-Package-Version",
			"X-Stainless-OS",
			"X-Stainless-Arch",
			"X-Stainless-Runtime",
			"X-Stainless-Runtime-Version",
			"X-Stainless-Retry-Count",
			"X-Stainless-Timeout",
			"X-Stainless-Helper-Method",
		) {
			deleteHeaderAllForms(h, k)
		}
		setHeaderRaw(h, "User-Agent", "sub2api-client/1.0")
		deleteHeaderAllForms(h, "anthropic-beta")
	default:
	}
}
