package claude

import "os"

// Hermes Agent 出站身份（API-key 路由 → 官方 Anthropic）。
//
// Hermes Agent（github.com/NousResearch/hermes-agent，agent/anthropic_adapter.py）使用
// Anthropic Python SDK 打官方 API-key 路由，出站形态为 SDK 默认头 + 两个基础 beta，
// 不携带任何 Claude Code 客户端特征（无 x-app / session 头 / claude-code beta /
// metadata.user_id）。本组常量复刻该形态，供 api_key 账号选择 outbound_identity
// = hermes_agent 时替换客户端透传的头集。
const (
	// HermesPinnedAnthropicSDKVersion 是 Hermes 锁定的 anthropic==0.87.0
	// （pyproject.toml: "anthropic==0.87.0"）。
	HermesPinnedAnthropicSDKVersion = "0.87.0"

	// HermesPythonVersion 是 Hermes 要求的 Python 3.14（.python-version）。
	HermesPythonVersion = "3.14"
)

// HermesBetaHeader 是 Hermes 对普通（API-key）Anthropic 路由的 anthropic-beta：
// _COMMON_BETAS（interleaved-thinking + fine-grained-tool-streaming），不含
// claude-code / oauth beta（那是 OAuth 路由专属）。
const HermesBetaHeader = BetaInterleavedThinking + "," + BetaFineGrainedToolStreaming

// hermesUserAgentVersionEnv 允许覆盖 UA 中的 SDK 版本号（默认 0.87.0）。
const hermesUserAgentVersionEnv = "SUB2API_HERMES_SDK_VERSION"

// hermesOSArchEnv 允许覆盖 x-stainless-os / x-stainless-arch 的取值。
const (
	hermesOSEnv   = "SUB2API_HERMES_STAINLESS_OS"
	hermesArchEnv = "SUB2API_HERMES_STAINLESS_ARCH"
)

// HermesUserAgent 返回 Anthropic Python SDK 的默认 User-Agent：
// f"{client_class}/Python {version}"，client_class 为 "Anthropic"。
func HermesUserAgent() string {
	version := HermesPinnedAnthropicSDKVersion
	if v := os.Getenv(hermesUserAgentVersionEnv); v != "" {
		version = v
	}
	return "Anthropic/Python " + version
}

// hermesStainlessOS 返回 x-stainless-os（SDK 的 platform.platform() 取值）。
func hermesStainlessOS() string {
	if v := os.Getenv(hermesOSEnv); v != "" {
		return v
	}
	return "Linux"
}

// hermesStainlessArch 返回 x-stainless-arch（SDK 的 platform.machine() 取值）。
func hermesStainlessArch() string {
	if v := os.Getenv(hermesArchEnv); v != "" {
		return v
	}
	return "x64"
}

// HermesHeaders 返回 Hermes（Anthropic Python SDK）的完整出站请求头集。
// 调用方负责认证头与 Content-Type；本组头以强制覆盖方式写入。
func HermesHeaders() map[string]string {
	return map[string]string{
		"User-Agent":                  HermesUserAgent(),
		"X-Stainless-Lang":            "python",
		"X-Stainless-Package-Version": HermesPinnedAnthropicSDKVersion,
		"X-Stainless-OS":              hermesStainlessOS(),
		"X-Stainless-Arch":            hermesStainlessArch(),
		"X-Stainless-Runtime":         "CPython",
		"X-Stainless-Runtime-Version": HermesPythonVersion,
		"X-Stainless-Retry-Count":     "0",
		"X-Stainless-Timeout":         "900",
		"X-Stainless-Async":           "false",
		"anthropic-version":           "2023-06-01",
		"anthropic-beta":              HermesBetaHeader,
	}
}

// StripClaudeClientHeaders 删除 Claude Code（js 客户端）特有的请求头：
// x-app、x-claude-code-session-id、anthropic-dangerous-direct-browser-access，
// 以及会话/追踪类可变头。Python SDK 客户端不发送这些头。
func StripClaudeClientHeaders(set func(string)) {
	for _, k := range []string{
		"X-App",
		"X-Claude-Code-Session-Id",
		"X-Client-Request-Id",
		"Anthropic-Dangerous-Direct-Browser-Access",
	} {
		set(k)
	}
}
