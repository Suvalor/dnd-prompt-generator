# DND Prompt Forge — LLM Multimodal Security PRD

> **Project**: DND Prompt Forge
> **Experiment ID**: 003
> **PRD Date**: 2026-06-02
> **Status**: Draft — awaiting value review gate
> **Value Review Ref**: docs/cognition/value-review.md

---

## 1. 项目概述

DND Prompt Forge 是一个面向 D&D 玩家的免费 SEO 落地应用，通过浏览器端确定性模板引擎将角色/场景描述转换为可直接粘贴到 AI 图像模型（Midjourney、ChatGPT、Gemini 等）的英文提示词。

**本次需求核心**：在保留现有浏览器端确定性生成器作为 fallback 的前提下，引入后端驱动的 LLM（LLM）文本生成能力，并构建完整的安全骨架（配额控制、滥用防护、密钥隔离）和多模态预留接口（图片/视频分析）。

---

## 2. 目标用户与使用场景

| 维度 | 描述 |
|------|------|
| **目标用户** | 泛 SEO 流量（匿名访客），无登录计划，未来不引入注册用户 |
| **使用场景** | 访客填写角色/场景表单 → 后端调用 OpenAI-compatible LLM API 生成提示词 → 复制粘贴到图像模型 |
| **商业约束** | 10次/小时配额是硬性成本限制，用于控制 OpenAI-compatible LLM API 费用 |
| **匿名性** | 完全匿名，不收集任何可识别个人信息 |

---

## 3. 核心功能列表

### P0 — MVP 必须交付（Phase 1 + Phase 2）

| # | 功能 | 描述 | 验收标准 |
|---|------|------|----------|
| P0.1 | 安全骨架 — 配额控制 | 每 IP / fingerprint / cookie 10次/小时配额 | 超过配额返回 429，配额重置逻辑正确 |
| P0.2 | 安全骨架 — 滥用防护 | 输入长度限制、速率限制、内容过滤 | 恶意输入被拦截，正常输入不受影响 |
| P0.3 | 安全骨架 — API 认证 | OpenAI-compatible LLM API 密钥通过环境变量注入，不硬编码 | 密钥不暴露在代码/日志中 |
| P0.4 | LLM 文本生成 | 后端调用 OpenAI-compatible LLM API 生成 D&D 提示词 | 返回格式与现有前端兼容，包含 main/short/negative/style/usage |
| P0.5 | Fallback 机制 | LLM 不可用时自动降级到浏览器端确定性生成器 | 网络故障/API 超时/密钥缺失时平滑降级 |
| P0.6 | 前端适配 | 前端调用后端 API 而非纯浏览器生成 | 保留现有 UI/UX，新增 loading/error 状态 |
| P0.7 | Docker Compose 本地开发 | 一键启动前后端 + 数据库 | `docker compose up` 成功运行 |

### P1 — 高优先级（Phase 2 增强）

| # | 功能 | 描述 | 验收标准 |
|---|------|------|----------|
| P1.1 | 配额持久化 | SQLite 记录每次 API 调用，支持跨重启配额追踪 | 重启后配额不丢失 |
| P1.2 | 配额前端展示 | 显示剩余配额、重置倒计时 | UI 实时反映配额状态 |
| P1.3 | 请求日志 | 记录输入输出用于调试和审计 | 敏感信息脱敏存储 |
| P1.4 | 错误处理增强 | 区分网络错误、API 错误、配额耗尽、内容审核拒绝 | 每种错误有明确用户提示 |

### P2 — 预留接口（Phase 3 迭代）

| # | 功能 | 描述 | 验收标准 |
|---|------|------|----------|
| P2.1 | 图片分析接口 | 上传图片 → LLM 分析 → 返回提示词建议 | 接口设计完成，可空实现 |
| P2.2 | 视频分析接口 | 上传视频 → LLM 分析 → 返回提示词建议 | 接口设计完成，可空实现 |
| P2.3 | 多模态预留架构 | 文件上传、异步处理、结果轮询机制 | 架构文档 + 接口定义 |

---

## 4. 功能边界（明确不做的事）

| # | 不做的事 | 理由 |
|---|---------|------|
| B1 | 用户注册/登录系统 | 保持完全匿名，降低复杂度 |
| B2 | 付费订阅/付费墙 | MVP 阶段免费，未来通过 Google AdSense 变现 |
| B3 | 图片/视频生成（非分析） | 只做提示词生成，不生成实际媒体文件 |
| B4 | 多语言输出（本次） | 仅英文提示词，UI 可保留英文 |
| B5 | 实时协作/共享 | 单人使用场景 |
| B6 | Phase 3 图片/视频分析的实际实现 | 仅预留接口和架构设计 |
| B7 | 替换现有浏览器端生成器 | 仅作为 fallback 保留，LLM 为优先路径 |

---

## 5. 技术约束与交付形式

### 5.1 技术栈

| 层级 | 技术 | 版本/说明 |
|------|------|----------|
| 前端 | React SPA (UMD via CDN) | 现有代码，不引入构建工具 |
| 后端 | Python FastAPI | 现有基础，扩展新端点 |
| 数据库 | SQLite | 配额/日志持久化 |
| LLM | OpenAI-compatible LLM API | 环境变量配置，部署时注入 |
| 容器 | Docker + Docker Compose | 本地开发 + 单 VPS 生产 |
| 反向代理 | Nginx | 现有配置，扩展 API 路由 |

### 5.2 环境变量

```bash
# OpenAI-compatible LLM API
LLM_API_KEY=                    # 部署时注入，本地开发可选
LLM_BASE_URL=                   # OpenAI-compatible LLM API 基础 URL
LLM_MODEL=                      # 模型名称

# 配额配置
QUOTA_HOURLY_LIMIT=10            # 每小时配额上限
QUOTA_WINDOW_SECONDS=3600        # 配额窗口（秒）

# 应用配置
APP_ENV=development|production   # 环境标识
LOG_LEVEL=INFO                   # 日志级别
```

### 5.3 部署目标

- **本地开发**：`docker compose up` 一键启动
- **生产部署**：单台 VPS，Docker Compose 部署
- **CI/CD**：暂不使用，手动部署

---

## 6. 验收标准（Acceptance Criteria）

### AC-1: 配额控制
```gherkin
Given 一个匿名用户
When 在 1 小时内发起第 11 次生成请求
Then 后端返回 HTTP 429 Too Many Requests
And 响应体包含 { "detail": "Quota exceeded. Try again in X minutes." }
```

### AC-2: LLM 文本生成
```gherkin
Given 有效的 OpenAI-compatible LLM API 配置
When 用户提交包含 race=Tiefling, class=Warlock 的生成请求
Then 后端在 10 秒内返回包含 main_prompt、short_prompt、negative_prompt、style_notes、usage_tip 的 JSON
And 提示词包含 D&D 特定术语
```

### AC-3: Fallback 降级
```gherkin
Given OpenAI-compatible LLM API 密钥缺失或 API 返回 5xx
When 用户发起生成请求
Then 后端返回 HTTP 200
And 响应体包含浏览器端确定性生成器的输出格式
And 前端无感知切换（UI 状态不变）
```

### AC-4: 安全 — 密钥隔离
```gherkin
Given 审查后端代码和日志
Then 找不到任何硬编码的 API 密钥
And 环境变量在容器中以 secrets 方式注入
And 日志中不包含完整 API 密钥
```

### AC-5: 前端适配
```gherkin
Given 用户在前端填写表单并点击 Generate
When 后端处理中
Then 前端显示 loading 状态（骨架屏）
When 后端返回成功
Then 前端显示生成的提示词，与现有 UI 一致
When 后端返回错误
Then 前端显示友好的错误信息，并提供重试按钮
```

### AC-6: Docker Compose 本地开发
```gherkin
Given 干净的开发环境
When 执行 docker compose up --build
Then 所有服务在 30 秒内启动
And 前端在 http://localhost:80 可访问
And 后端 API 在 http://localhost:8000 可访问
And 前后端通信正常
```

### AC-7: 多模态预留接口
```gherkin
Given 后端服务运行中
When 访问 POST /api/analyze-image（或 /api/analyze-video）
Then 返回 501 Not Implemented
And 响应体包含 { "detail": "Image analysis coming in Phase 3." }
```

---

## 7. Sprint 规划建议

### Sprint 1: 安全骨架（Phase 1）
- **目标**：配额系统 + 滥用防护 + 密钥管理
- **交付物**：
  - 配额中间件（IP/fingerprint/cookie 三维度）
  - SQLite 配额表
  - 环境变量配置模块
  - 安全测试（渗透测试配额绕过）

### Sprint 2: LLM 文本生成（Phase 2）
- **目标**：OpenAI-compatible LLM API 集成 + Fallback 机制 + 前端适配
- **交付物**：
  - OpenAI-compatible LLM API 客户端封装
  - `/api/generate-prompt` 端点（LLM 优先，fallback 兜底）
  - 前端 API 调用层
  - 错误处理和 loading 状态

### Sprint 3: 增强与预留（Phase 2.5 + Phase 3 接口）
- **目标**：配额持久化 + 前端展示 + 多模态预留接口
- **交付物**：
  - 配额前端组件
  - 请求日志系统
  - 图片/视频分析接口定义（501 占位）
  - 架构文档

### Sprint 4: 集成测试与部署
- **目标**：端到端测试 + 生产部署
- **交付物**：
  - Docker Compose 生产配置
  端到端测试套件
  - 部署文档
  - 性能基准测试

---

## 8. 风险识别

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| **R1: OpenAI-compatible LLM API 稳定性** | 高 | Fallback 机制确保服务可用；监控 API 健康状态 |
| **R2: 配额绕过** | 高 | 多维度配额（IP + fingerprint + cookie）；SQLite 持久化 |
| **R3: 密钥泄露** | 高 | 环境变量注入；日志脱敏；容器 secrets 管理 |
| **R4: 前端构建复杂度** | 中 | 保持现有 UMD + CDN 方案，不引入构建工具 |
| **R5: 成本超支** | 中 | 10次/小时硬限制；监控 API 调用量；告警机制 |
| **R6: SEO 影响** | 低 | 确保 SSR 或预渲染不影响；保持现有 meta 标签 |
| **R7: 浏览器兼容性** | 低 | 保持现有兼容性目标（现代浏览器） |

---

## 9. 依赖关系

```
Sprint 1 (安全骨架)
    |
    v
Sprint 2 (LLM 文本生成)
    |
    v
Sprint 3 (增强 + 预留接口)
    |
    v
Sprint 4 (集成测试 + 部署)
```

---

## 10. 附录

### A. 现有端点评阅

| 端点 | 方法 | 状态 | 说明 |
|------|------|------|------|
| `/api/health` | GET | 现有 | 健康检查 |
| `/api/generate-prompt` | POST | OpenAI-compatible LLM | 添加 fallback |
| `/api/feedback` | POST | 现有 | 保留 |
| `/api/memory-rules` | GET | 现有 | 保留 |
| `/api/analyze-image` | POST | 新增（预留） | 501 占位 |
| `/api/analyze-video` | POST | 新增（预留） | 501 占位 |

### B. 数据模型变更

**新增表：`quota_usage`**
```sql
CREATE TABLE quota_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    fingerprint TEXT,
    cookie_id TEXT,
    endpoint TEXT NOT NULL,
    created_at TEXT NOT NULL,
    user_agent TEXT
);

CREATE INDEX idx_quota_ip ON quota_usage(ip_address, created_at);
CREATE INDEX idx_quota_fingerprint ON quota_usage(fingerprint, created_at);
CREATE INDEX idx_quota_cookie ON quota_usage(cookie_id, created_at);
```

**新增表：`request_logs`**
```sql
CREATE TABLE request_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL UNIQUE,
    ip_address TEXT,
    endpoint TEXT,
    input_summary TEXT,  -- 脱敏后的输入摘要
    output_summary TEXT,   -- 脱敏后的输出摘要
    status TEXT,          -- success | fallback | error
    error_message TEXT,   -- 错误信息（不含敏感数据）
    duration_ms INTEGER,
    created_at TEXT
);
```

---

*End of PRD*
