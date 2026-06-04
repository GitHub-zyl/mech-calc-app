# `/api/history` 接口文档

> 机械设计计算小程序 - 计算历史持久化 REST API
>
> 状态: 稳定 (v2.2.0 起, 计划 [2026-06-03-p0-p1-history-formulas.md](../superpowers/plans/2026-06-03-p0-p1-history-formulas.md))
>
> 存储: SQLite (WAL 模式), 路径 `data/history.db` (测试环境: `data/test_history.db`)

---

## 概述

`/api/history` 提供计算历史的持久化与查询能力。前端在每次计算后通过 `POST` 上报一次记录, 后续通过 `GET` 列表分页查询, 也可按 `category / calc_id / 时间区间` 筛选。`DELETE` 用于清理过期数据, `GET /stats` 用于统计概览。

所有响应遵循统一格式 `backend/api/responses.py`:

```jsonc
// 成功
{ "status": "ok", "data": ..., "meta": {...} }

// 失败
{ "status": "error", "message": "...", "code": 400, "details": ... }
```

---

## 数据模型

### `calc_history` 表

| 字段         | 类型     | 必填 | 说明                                    |
| ------------ | -------- | ---- | --------------------------------------- |
| `id`         | INTEGER  | 自增 | 主键                                    |
| `ts`         | REAL     | 是   | Unix timestamp (秒, 浮点)                |
| `category`   | TEXT     | 是   | 分类, 如 `gear` / `bearing` / `weld`     |
| `endpoint`   | TEXT     | 是   | 计算端点路径, 如 `/api/calc/gear/spur`   |
| `calc_id`    | TEXT     | 否   | 前端注册表 id                            |
| `input_json` | TEXT     | 是   | 输入参数 (JSON 序列化)                   |
| `output_json`| TEXT     | 是   | 输出结果 (JSON 序列化)                   |
| `client_ip`  | TEXT     | 否   | 客户端 IP (取自 `X-Forwarded-For` 优先) |
| `duration_ms`| REAL     | 否   | 计算耗时 (毫秒)                         |

索引: `idx_calc_history_ts` (ts DESC), `idx_calc_history_cat` (category)

---

## 端点

### 1. `POST /api/history` — 新增记录

**请求体**

```json
{
  "category": "gear",
  "endpoint": "/api/calc/gear/spur",
  "calc_id": "gear-spur",
  "input": { "module": 2, "teeth": 20 },
  "output": { "d_pitch_mm": 40, "da_mm": 44 },
  "duration_ms": 1.5
}
```

**字段约束**

| 字段         | 必填 | 说明                                  |
| ------------ | ---- | ------------------------------------- |
| `category`   | ✅   | 非空字符串, 去除首尾空白              |
| `endpoint`   | ✅   | 非空字符串, 去除首尾空白              |
| `input`      | ✅   | 任意可 JSON 序列化的对象 (可空 dict)  |
| `output`     | ✅   | 任意可 JSON 序列化的对象 (可空 dict)  |
| `calc_id`    | ❌   | 前端注册表 id                         |
| `duration_ms`| ❌   | 浮点型, 用于性能分析                  |

**响应 200**

```json
{
  "status": "ok",
  "data": {
    "id": 42,
    "record": {
      "id": 42,
      "ts": 1717400000.123,
      "category": "gear",
      "endpoint": "/api/calc/gear/spur",
      "calc_id": "gear-spur",
      "input": { "module": 2, "teeth": 20 },
      "output": { "d_pitch_mm": 40, "da_mm": 44 },
      "client_ip": "127.0.0.1",
      "duration_ms": 1.5
    }
  },
  "meta": { "created": true }
}
```

**错误 400**

| 触发条件                          | message                  |
| --------------------------------- | ------------------------ |
| 缺 `category` 或为空              | `category 和 endpoint 必填` |
| 缺 `endpoint` 或为空              | `category 和 endpoint 必填` |
| 缺 `input` / `output`             | `input 和 output 必填`   |
| Body 不是合法 JSON                | (无 body)                |
| 数据库层 `ValueError`             | (透传 message)           |

**示例**

```bash
curl -X POST http://127.0.0.1:9091/api/history \
  -H "Content-Type: application/json" \
  -d '{
    "category": "gear",
    "endpoint": "/api/calc/gear/spur",
    "input": {"module": 2, "teeth": 20},
    "output": {"d_pitch_mm": 40}
  }'
```

---

### 2. `GET /api/history` — 列表 (分页+筛选)

**Query 参数**

| 参数       | 类型    | 默认  | 约束                | 说明                            |
| ---------- | ------- | ----- | ------------------- | ------------------------------- |
| `limit`    | int     | 20    | 1 ≤ limit ≤ 200     | 单页条数, 越界自动规整          |
| `offset`   | int     | 0     | ≥ 0                 | 偏移量                          |
| `category` | string  | —     | 精确匹配            | 按分类筛选                      |
| `calc_id`  | string  | —     | 精确匹配            | 按前端注册表 id 筛选            |
| `since`    | float   | —     | Unix timestamp      | 仅返回 `ts >= since` 的记录     |
| `until`    | float   | —     | Unix timestamp      | 仅返回 `ts <= until` 的记录     |

**响应 200**

```json
{
  "status": "ok",
  "data": {
    "items": [
      {
        "id": 42,
        "ts": 1717400000.123,
        "category": "gear",
        "endpoint": "/api/calc/gear/spur",
        "calc_id": "gear-spur",
        "input": {...},
        "output": {...},
        "client_ip": "127.0.0.1",
        "duration_ms": 1.5
      }
    ],
    "pagination": {
      "limit": 20,
      "offset": 0,
      "total": 137,
      "has_more": true
    }
  }
}
```

排序: 按 `ts DESC` (新→旧).

**错误 400** — `limit` / `offset` 非整数

**示例**

```bash
# 第 1 页, 每页 20 条, 仅看 gear 类
curl 'http://127.0.0.1:9091/api/history?limit=20&offset=0&category=gear'

# 时间区间
curl 'http://127.0.0.1:9091/api/history?since=1717400000&until=1717500000'
```

---

### 3. `GET /api/history/<id>` — 详情

**路径参数** `id` — 整数主键

**响应 200**: 完整记录 (字段同 POST 响应)

**错误 404**: `{ "status": "error", "code": 404, "message": "记录 <id> 不存在" }`

---

### 4. `DELETE /api/history/<id>` — 删除单条

**响应 200**: `{ "status": "ok", "data": { "id": 42, "deleted": true } }`

**错误 404**: 记录不存在

---

### 5. `DELETE /api/history` — 批量删除 / 清空

**Query 参数**

- `ids=1,2,3` — 逗号分隔的 id 列表
- `all=1` — 清空所有记录

**响应 200 (批量)**

```json
{ "status": "ok", "data": { "requested": 3, "deleted": 3 } }
```

**响应 200 (清空)**

```json
{ "status": "ok", "data": { "cleared": 137 } }
```

**错误 400**: 同时无 `ids` 也无 `all` / `ids` 包含非整数

**示例**

```bash
# 批量
curl -X DELETE 'http://127.0.0.1:9091/api/history?ids=1,2,3'

# 清空 (慎用, 通常只用于测试)
curl -X DELETE 'http://127.0.0.1:9091/api/history?all=1'
```

---

### 6. `GET /api/history/stats` — 统计

**响应 200**

```json
{
  "status": "ok",
  "data": {
    "total": 137,
    "by_category": {
      "gear": 50,
      "bearing": 40,
      "weld": 30,
      "shaft": 17
    }
  }
}
```

---

### 7. `GET /api/history/categories` — 实际分类清单

返回**已有数据中**出现过的分类 (派生自 `stats_by_category`, 不依赖静态清单).

**响应 200**: `{ "status": "ok", "data": ["bearing", "gear", "shaft", "weld"] }`

---

## 事务与一致性

- 单条 INSERT 使用隐式事务 (每条语句自动 commit)
- `init_db()` 启用 `PRAGMA journal_mode=WAL`, 提升并发读写
- 索引保证分页/筛选在大数据量下不退化 (按 `ts DESC` 已建索引)
- 所有写操作均经过 `try/except` 捕获, 失败时返回 400/500 而非崩溃

## 性能

- 单次 `POST`: 典型 < 1ms (本地 SQLite + WAL)
- 列表查询 (20 条, 索引命中): 典型 < 1ms
- 数据库文件位置: `data/history.db` (生产) / `data/test_history.db` (测试)

## 客户端集成示例 (Python)

```python
import requests
BASE = "http://127.0.0.1:9091"

# 1. 上报
r = requests.post(f"{BASE}/api/history", json={
    "category": "gear",
    "endpoint": "/api/calc/gear/spur",
    "input": {"module": 2, "teeth": 20},
    "output": {"d_pitch_mm": 40},
    "duration_ms": 1.2,
})
rec = r.json()["data"]["record"]
print(f"saved id={rec['id']}")

# 2. 查询最近 10 条 gear 类
r = requests.get(f"{BASE}/api/history", params={
    "category": "gear", "limit": 10,
})
for item in r.json()["data"]["items"]:
    print(item["id"], item["input"])

# 3. 统计
r = requests.get(f"{BASE}/api/history/stats")
print(r.json()["data"])
```

## 错误码速查

| code | 含义                              |
| ---- | --------------------------------- |
| 200  | 成功                              |
| 400  | 请求参数错误 (必填/类型/格式)     |
| 404  | 资源不存在 (id 无效)              |
| 500  | 服务器内部错误 (DB 不可用等)      |

## 测试覆盖

- 单元测试: `backend/tests/unit/test_history_db.py` (21 用例)
- 集成测试: `backend/tests/integration/test_api_history.py` (27 用例)
- 覆盖率: `backend/database/history_db.py` 92%, `backend/api/history.py` 97%
