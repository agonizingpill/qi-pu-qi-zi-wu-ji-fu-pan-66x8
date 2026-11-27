# 棋谱棋子误记复盘

合川围棋裁判组保留原棋谱，将筛出的手次交给棋盘重放，并把提子差写入有签认的勘误簿。

## 现场工作与联系人

模拟客户为合川围棋裁判组。赛事对局、棋钟手次、误记嫌疑分类、裁判勘误；提子冲突未重放禁止锁定勘误。

- 对局原件 `matches`，字段为 `white`（白方）、`black`（黑方）、`round_no`（轮次）、`open`（复核中）。模型约束位于 `backend/domain/matches_model.py`，规则位于 `matches_service.py`。
- 棋钟与手次 `plies`，字段为 `game`（对局）、`number`（手次）、`gap`（棋钟差秒）、`capture_claim`（记录提子数）、`replayed`（重放提子数）、`repeat_move`（重复落点）、`witness`（已重放）、`adjudicated`（勘误后确认）。模型约束位于 `backend/domain/plies_model.py`，规则位于 `plies_service.py`。
- 嫌疑签条 `referee_flags`，字段为 `ply`（手次号）、`reason`（模型复核方向）、`holdout`（留出正确率）、`token`（计算号）。模型约束位于 `backend/domain/referee_flags_model.py`，规则位于 `referee_flags_service.py`。
- 裁判勘误本 `errata`，字段为 `flag`（嫌疑签条）、`official`（签认提子数）、`corrigendum`（勘误说明）。模型约束位于 `backend/domain/errata_model.py`，规则位于 `errata_service.py`。

团队为模拟的6 人裁判组，维护业余联赛现场棋谱。

棋钟、转录格和裁判手写更正单分开登记。跳手时序难定位，提子票据可能和实盘不符，封账后难证明勘误采用了哪次重放。

原始手次和裁判重放进入复盘台，比赛记录员签发可追溯的正式勘误。

### 一天的业务操作

1. 09:00 查阅 G-41 黑白双方原始谱。
2. 09:20 登记第 32 手，记录提子四枚。
3. 10:00 计算嫌疑类别。
4. 11:00 把疑似重复落点锁定到 FLAG-44。
5. 13:00 重放前签认被拒绝。
6. 13:30 裁判重放，发现仅提两枚。
7. 14:00 签发 ER-44，原谱提子数字仍保留。

## 启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

打开 `http://127.0.0.1:18314`。FastAPI OpenAPI 在 `http://127.0.0.1:19314/docs`。
Compose 运行 Nginx、Python FastAPI、独立 Redis 消费进程、SQL 数据库和 Redis，SQL 与 Redis 使用命名卷。
本机开发时，在 Python 3.11 环境安装 `backend/requirements.txt` 后从 backend 目录运行 `uvicorn core.app:app`。须提供 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`，`SEED_DEMO` 控制演示初始化。

| 演示账号 | 权限 |
|---|---|
| operator@demo.test | 提交领域记录和计算请求 |
| reviewer@demo.test | 提交记录并执行有业务约束的复核操作 |
| viewer@demo.test | 浏览业务台账 |

三个本地演示账号均使用 `DemoC0de!2026`。角色在 `backend/core/roles.py` 和 `frontend/src/store.js` 中声明。计算状态在 worker、queueing、API 和同一前端 store 中使用。

## 页面与接口

| 业务任务 | FastAPI 路由 | 页面 |
|---|---|---|
| 对局原件 | `/matches` /matches/review-window | `frontend/src/pages/matches.js` |
| 棋钟与手次 | `/plies` /plies/attach-ply，/plies/verify-replay | `frontend/src/pages/plies.js` |
| 复盘派单台 | `/dispatch_orders` /dispatch_orders/plan，/claim，/swap，/report | `frontend/src/pages/plies.js` |
| 嫌疑签条 | `/referee_flags` /referee_flags/triage，/referee_flags/attach-flag | `frontend/src/pages/referee_flags.js` |
| 裁判勘误本 | `/errata` /errata/issue-erratum | `frontend/src/pages/errata.js` |

复盘只有三张桌，派单在 `backend/domain/dispatch_service.py` 中维护，模型约束在 `dispatch_model.py`：

- **派单**：`/dispatch_orders/plan` 按 SGD hinge 对每手次的「核对提子」判别分从高到低补满空桌；每局最多占一桌，取该局最高分的一个手次。已重放（`witness`）或已封账的手次不再派。
- **换单与领单**：两者在同一派单顾问锁下提交，先落库者生效。先领到即按原单做（`claimed` 后不可换）；先换成的高分手次撤下原单，原领单须重新领。
- **报数腾桌**：`/dispatch_orders/report` 由领单人报完实盘提子数（`done`）后才腾桌，同时把重放数写回手次。
- **封账**：关闭复盘窗口时调用 `release_for_seal`，已领未报数的手次拦住封账，其余未领的单一律撤回。
- **中断恢复**：应用启动时执行一次 `plan`，收敛中断遗留的桌位；已重放或已封账的手次不再派。表中两个部分唯一索引（桌号、对局）在库层兜底一桌一单、一局一桌。

SQL 实体与约束在 `backend/domain` 下维护。前端使用原生 ES modules。核心算子为 SGDClassifier hinge。在固定种子生成的三类模拟原件特征上训练 SGD hinge，按类留出 27 条，回传判别分数。派单取「核对提子」类的判别分作为优先级分数。

棋谱手次只记录统计特征，线下重放负责核对围棋规则。

[MIT](LICENSE)
