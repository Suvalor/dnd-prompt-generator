# 项目需求文档（PRD）

## 项目概述
将 DND Prompt Forge 前端的 Generate 按钮从纯本地 FORGE.build() 调用改为调用后端 FastAPI API，实现 LLM 生成 + fallback + 配额控制的完整业务闭环。

## 目标用户与使用场景
- **目标用户**：通过 Google SEO 访问 dndpromptforge.com 的匿名用户，无需登录
- **使用场景**：用户填写表单（race/class/style/mood 等），点击 Generate，前端调用后端 /api/generate-prompt 获取 LLM 增强的提示词；当 LLM 不可用或配额耗尽时自动 fallback 到确定性生成；前端展示当前模式（LLM/fallback）和剩余额度

## 核心功能列表（P0/P1/P2优先级）

### P0: 业务闭环（5 项，必须完成）
1. **Frontend bootstrap session**：页面加载时调用 POST /api/session/bootstrap，存储 session cookie 和 CSRF token，获取 features 配置（llm_enabled, quota_limit 等）
2. **Generate 按钮接入后端 API**：点击 Generate 时调用 POST /api/generate-prompt，携带 CSRF header (x-csrf-token) 和字段映射后的请求体；LLM 成功时展示 LLM 结果，LLM 失败时 fallback 到 FORGE.build() 本地生成
3. **Browser fingerprint hash**：使用 crypto.subtle.digest SHA-256 生成浏览器指纹哈希，随 generate-prompt 请求发送 client_fingerprint_hash 字段
4. **Quota 超限 fallback 处理**：后端返回 mode=fallback + quota.remaining=0 时，前端正确展示 fallback 结果并提示用户
5. **Mode 和 quota 展示**：SuccessState 中显示 LLM/fallback mode 标识和剩余额度（remaining / limit）

### P1: 部署配置（重要但可延后）
6. **Nginx API proxy**：在 nginx.conf 中添加 /api/ location 代理到 backend:8000
7. **.env.example**：包含所有 MiMo 变量的示例环境变量文件
8. **docker-compose.yml 更新**：确保环境变量和端口配置正确

### P2: 集成测试（锦上添花）
9. **Business integration tests**：4 类测试——bootstrap session、generate prompt、auth headers、quota exceeded

## 功能边界（明确不做的事）
- 不新增后端端点或修改后端业务逻辑（后端已就绪）
- 不重设计前端 UI 或表单结构
- 不新增 SEO 长尾页面
- 不改造反馈循环（feedback 按钮暂时保持前端本地行为）
- 不引入 npm/webpack/vite 等构建工具
- 不做 SSR 或服务端渲染
- 不做 rate limiting 的前端节流（后端已有 quota 控制）

## 技术约束与交付形式

### 技术栈
- **前端**：React 18 (Babel JSX in-browser), 无构建工具，脚本通过 `<script type="text/babel">` 加载
- **后端**：FastAPI + Redis + SQLite（已实现，不改）
- **部署**：Docker Compose（nginx:alpine + backend + redis:7-alpine）
- **API 通信**：fetch API, JSON, CORS with credentials

### 字段映射（前端 → 后端）
| 前端表单字段 | 后端 API 字段 |
|---|---|
| type | output_type |
| klass | class_role |
| desc | description |
| model | target_model |
| race | race (同名) |
| style | style (同名) |
| mood | mood (同名) |
| gender | gender (同名) |
| age | age (同名) |
| alignment | alignment (同名) |
| armor | armor (同名) |
| weapon | weapon (同名) |
| magic | magic (同名) |
| palette | palette (同名) |
| camera | camera (同名) |
| (computed) | client_fingerprint_hash |
| (computed) | fallback_prompt_preview |

### 安全约束
- 所有 mutating 请求必须携带 x-csrf-token header（bootstrap 获取的签名 token）
- Session cookie (session_id) 由后端 Set-Cookie 自动管理（httpOnly, SameSite=Lax）
- Quota 检查失败时 fail-closed：不调 LLM，返回 fallback，记录审计日志

### 交付物
- 修改后的前端文件（api-client.js, generator.jsx, app.jsx）
- 更新后的 nginx.conf（添加 /api/ proxy_pass）
- .env.example 文件
- 更新后的 docker-compose.yml（如有必要）

## 验收标准（可量化的AC列表）
- [ ] AC1: 页面加载后自动调用 /api/session/bootstrap，前端内存中持有 csrf_token 和 features 配置
- [ ] AC2: 点击 Generate 按钮，前端发送 POST /api/generate-prompt，请求头包含 x-csrf-token，请求体字段正确映射
- [ ] AC3: 后端返回 mode=llm 时，前端展示 LLM 生成的提示词（main_prompt, short_prompt, negative_prompt, style_notes, usage_tip）
- [ ] AC4: 后端返回 mode=fallback 时，前端展示 fallback 提示词，并在 UI 中标注 "Fallback mode"
- [ ] AC5: 后端不可达或网络错误时，前端 fallback 到本地 FORGE.build() 并展示本地结果
- [ ] AC6: 前端生成并发送 client_fingerprint_hash（SHA-256 指纹哈希）
- [ ] AC7: SuccessState 中显示当前 mode（LLM / Fallback）和剩余额度（如 "7 / 10 remaining"）
- [ ] AC8: docker compose up 后，前端通过 nginx proxy 成功访问后端 API
- [ ] AC9: Quota 耗尽时（remaining=0），前端仍能获取 fallback 结果并正确展示

## Sprint规划建议

### Sprint 1: 业务闭环核心（P0 全部）
1. 新建 api-client.js：bootstrap(), generatePrompt(), getQuotaStatus(), fingerprint hash
2. 改造 generator.jsx：runGenerate() 改为 API 调用 + fallback 逻辑
3. 改造 app.jsx：mount 时 bootstrap session
4. SuccessState 新增 mode badge + quota display

### Sprint 2: 部署配置 + 集成测试（P1 + P2）
1. nginx.conf 添加 /api/ proxy_pass
2. .env.example 更新
3. docker-compose.yml 验证
4. 集成测试编写

## 风险识别
1. **CSRF 中间件阻断**：前端必须正确携带 x-csrf-token，否则所有 mutating 请求返回 403；缓解：bootstrap 后立即存储 token，每次请求从内存读取
2. **Babel in-browser 编译**：新增 api-client.js 必须使用 `<script type="text/babel">` 加载，且需在 generator.jsx 之前；缓解：确认 script 加载顺序
3. **Nginx 缺少 API proxy**：当前 nginx.conf 没有 /api/ 路由，docker 环境下前端无法访问后端；缓解：Sprint 1 开发阶段可直连 localhost:8000，Sprint 2 补 nginx proxy
4. **Fingerprint 稳定性**：crypto.subtle 在非 HTTPS 环境可能不可用；缓解：fingerprint 生成失败时传空字符串，后端已有 null 容错
5. **CORS 凭证**：fetch 请求必须 credentials: 'include' 才能携带 cookie；缓解：api-client.js 中统一设置

value_review_ref: docs/cognition/value-review.md