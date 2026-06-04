# `/api/formulas` 接口文档

> 机械设计计算小程序 - 公式查询 REST API
>
> 状态: 稳定 (v2.2.0 起, 计划 [2026-06-03-p0-p1-history-formulas.md](../superpowers/plans/2026-06-03-p0-p1-history-formulas.md))
>
> 数据源: `backend/calculations/formulas_data.py` (30+ 条静态公式)

---

## 概述

`/api/formulas` 提供工程常用公式的浏览、搜索、详情查询、相关推荐和**数值求解**能力。`POST /<id>/solve` 是核心创新点 —— 已知公式中 N-1 个变量, 自动反解第 N 个变量 (例如: 已知 `m=10, a=2` 反求 `F`).

适用场景:

- 教学 / 参考手册 (查公式 + 单位)
- 现场计算 (查公式 + 求解)
- 工程助手 (推荐相关公式)

---

## 公式数据模型

每条公式包含:

```json
{
  "id": "fma",
  "name_zh": "牛顿第二定律",
  "name_en": "Newton's Second Law",
  "formula": "F = m · a",
  "expr": "F = m * a",
  "variables": {
    "F": { "name": "合外力", "unit": "N" },
    "m": { "name": "质量", "unit": "kg" },
    "a": { "name": "加速度", "unit": "m/s²" }
  },
  "unknowns": ["F", "m", "a"],
  "category": "mechanics",
  "description": "物体加速度与所受合外力成正比",
  "tags": ["力学", "动力学", "牛顿", "基础"],
  "related": ["pfa", "pfg"],
  "reference": "理论力学(哈工大) §2.1"
}
```

## 分类清单

| 分类 (id)        | 中文     | 典型公式                   |
| ---------------- | -------- | -------------------------- |
| `mechanics`    | 力学     | F=ma, p=F/A, G=mg, f=μN    |
| `kinematics`   | 运动学   | s=vt, v=v₀+at, a=v²/r      |
| `energy`       | 能量     | W=Fs, P=Fv, P=Tω, Ek, Ep   |
| `rotation`     | 旋转     | ω=2πn/60, v=ωr, T=9550P/n  |
| `strength`     | 强度     | σ=F/A, τ=T/Wp, σ=M/W       |
| `fluid`        | 流体     | Q=Av, 伯努利, 雷诺数       |
| `geometry`     | 几何     | 圆面积/周长/圆柱体积       |
| `thermal`      | 热       | Q=cmΔT, ΔL=αLΔT            |
| `vibration`    | 振动     | 弹簧振子周期, 单摆周期     |

---

## 端点

### 1. `GET /api/formulas` — 列表 (搜索+分类筛选)

**Query 参数**

| 参数       | 类型   | 默认 | 说明                                              |
| ---------- | ------ | ---- | ------------------------------------------------- |
| `q`        | string | —    | 模糊匹配 id / name_zh / name_en / formula / tags |
| `category` | string | —    | 精确分类匹配                                      |

**匹配规则** (大小写不敏感):

- `q` 是子串匹配, 不是全文索引
- 匹配字段优先级: `id` > `name_zh` > `name_en` > `formula` > `tags`
- `q` 和 `category` 同时存在时取交集 (AND)

**响应 200**

```json
{
  "status": "ok",
  "data": {
    "items": [ {公式对象}, ... ],
    "total": 4,
    "q": "圆",
    "category": "geometry"
  }
}
```

**示例**

```bash
# 全部
curl http://127.0.0.1:9091/api/formulas

# 按分类
curl 'http://127.0.0.1:9091/api/formulas?category=mechanics'

# 按关键字 (匹配中文名 / 英文名 / 标签)
curl 'http://127.0.0.1:9091/api/formulas?q=牛顿'

# 组合
curl 'http://127.0.0.1:9091/api/formulas?q=圆&category=geometry'
```

---

### 2. `GET /api/formulas/categories` — 分类清单

**响应 200**: `{ "status": "ok", "data": ["mechanics", "kinematics", "energy", ...] }` (按字母序)

---

### 3. `GET /api/formulas/<id>` — 详情

**路径参数** `id` — 公式 id (如 `fma`)

**响应 200**: 完整公式对象

**错误 404**: `{ "status": "error", "code": 404, "message": "公式 <id> 不存在" }`

**示例**

```bash
curl http://127.0.0.1:9091/api/formulas/fma
```

---

### 4. `GET /api/formulas/<id>/related` — 相关公式

按公式的 `related` 字段返回相关条目 (并自动展开为完整对象).

**响应 200**

```json
{
  "status": "ok",
  "data": {
    "formula_id": "fma",
    "related": [
      { "id": "pfa", "name_zh": "压强公式", ... },
      { "id": "pfg", "name_zh": "重力", ... }
    ]
  }
}
```

**错误 404**: 公式不存在

---

### 5. `POST /api/formulas/<id>/solve` — 数值求解 (核心)

根据已知量, 自动反解公式中**唯一一个未知变量**.

**请求体**

```json
{ "given": { "m": 10, "a": 2 } }
```

**求解规则**

1. 公式的所有变量 = `defaults` + `given`
2. 未知变量 = `公式所有变量 - 上面集合`
3. 若未知数 = 0: 返回一致性校验 (无需求解)
4. 若未知数 = 1: 计算 lhs
5. 若未知数 > 1: 报错, 列出所有缺失变量

**响应 200**

```json
{
  "status": "ok",
  "data": {
    "ok": true,
    "target": "F",
    "value": 20.0,
    "result": { "F": 20.0, "m": 10.0, "a": 2.0 },
    "formula": "F = m · a",
    "unit": "N"
  }
}
```

**响应 400 (已知量不足)**

```json
{
  "status": "error",
  "code": 400,
  "message": "已知量 不足, 还缺 2 个变量: ['F', 'a']",
  "details": ["F", "a"]
}
```

**响应 400 (其他错误)**

| 触发条件                       | message 示例                                  |
| ------------------------------ | --------------------------------------------- |
| `given` 不是 dict              | `given 必须为 dict`                           |
| `given` 中的值无法转 float     | `given 数值转换失败: could not convert ...`   |
| 公式不支持反解 (目标非 lhs)    | `公式暂不支持反解 <var>, 请手动使用 <formula>` |
| 求值时异常 (除零等)            | `求值失败: <原因>`                            |

**响应 404**: 公式不存在

**示例**

```bash
# F=ma, 已知 m=10, a=2 求 F
curl -X POST http://127.0.0.1:9091/api/formulas/fma/solve \
  -H "Content-Type: application/json" \
  -d '{"given": {"m": 10, "a": 2}}'
# → {"target": "F", "value": 20.0, ...}

# P=Fv, 已知 F, v 求 P
curl -X POST http://127.0.0.1:9091/api/formulas/pfv/solve \
  -H "Content-Type: application/json" \
  -d '{"given": {"F": 100, "v": 5}}'
# → {"target": "P", "value": 500.0, ...}

# 重力 G=mg, 已知 m=10 (g 用默认值 9.81)
curl -X POST http://127.0.0.1:9091/api/formulas/pfg/solve \
  -H "Content-Type: application/json" \
  -d '{"given": {"m": 10}}'
# → {"target": "G", "value": 98.1, ...}

# 圆面积 A=πd²/4, 已知 d=10 求 A
curl -X POST http://127.0.0.1:9091/api/formulas/circle_area/solve \
  -H "Content-Type: application/json" \
  -d '{"given": {"d": 10}}'
# → {"target": "A", "value": 78.5398..., ...}
```

### 求解能力范围与限制

| 情况                              | 支持  | 说明                                                |
| --------------------------------- | ----- | --------------------------------------------------- |
| 反解 LHS 变量 (F=ma → 求 F)       | ✅    | 主流情况                                            |
| 全部已知                          | ✅    | 返回一致性确认                                      |
| 已知 N-1 个, N≥4                  | ✅    | 自动补默认值                                        |
| 已知 < N-1                        | ❌    | 报错 + 列出所有缺失变量                            |
| 反解 RHS 中的变量 (F=ma → 求 a)   | ⚠️   | 当前实现仅支持 LHS 反解                            |
| 隐式方程 (伯努利)                 | ⚠️   | 列出但 `solve` 不支持, 用计算引擎                   |

---

## 错误码速查

| code | 含义                                |
| ---- | ----------------------------------- |
| 200  | 成功                                |
| 400  | 请求参数错误 (given 类型/数值/不足) |
| 404  | 公式 id 不存在                      |

## 扩展性

新增公式只需在 `backend/calculations/formulas_data.py` 的 `FORMULAS` 列表中追加一条 dict:

```python
{
    'id': 'my_formula',
    'name_zh': '我的公式',
    'name_en': 'My Formula',
    'formula': 'y = k·x + b',         # 显示用
    'expr': 'y = k * x + b',           # 求值用 (Python 表达式)
    'variables': {
        'y': {'name': '...', 'unit': '...'},
        'k': {'name': '...', 'unit': '...', 'default': 1.0},  # 可选默认
        'x': {'name': '...', 'unit': '...'},
        'b': {'name': '...', 'unit': '...'},
    },
    'unknowns': ['y', 'k', 'x', 'b'],
    'category': 'mechanics',
    'description': '...',
    'tags': ['...', '...'],
    'related': ['fma', 'pfa'],
    'reference': '...',
}
```

**约束**:

- `id` 全局唯一
- `expr` 必须是合法 Python 表达式, **仅可**使用 `variables` 中定义的标识符
- `unknowns` 中的每个变量必须出现在 `variables` 中
- `related` 中的每个 id 必须存在

启动后 API 自动可用, 无需重启数据库 (公式在内存中). 服务重启后新公式生效.

## 测试覆盖

- 单元测试: `backend/tests/unit/test_calculations_formulas.py` (41 用例)
  - 覆盖所有分类的 `solve` 调用
  - 覆盖反解失败/公式不存在/数据完整性
- 集成测试: `backend/tests/integration/test_api_formulas.py` (24 用例 + 1 skip)
  - 覆盖所有 7 个端点的正常/异常路径
- 覆盖率:
  - `backend/calculations/formulas_data.py` 96%
  - `backend/api/formulas.py` 100%

## 客户端示例 (Python)

```python
import requests
BASE = "http://127.0.0.1:9091"

# 1. 搜索公式
r = requests.get(f"{BASE}/api/formulas", params={"q": "牛顿"})
for f in r.json()["data"]["items"]:
    print(f["id"], f["formula"])

# 2. 获取详情
f = requests.get(f"{BASE}/api/formulas/fma").json()["data"]
print(f["description"])

# 3. 数值求解
r = requests.post(f"{BASE}/api/formulas/fma/solve",
                  json={"given": {"m": 10, "a": 2}})
result = r.json()["data"]
print(f"{result['target']} = {result['value']} {result['unit']}")

# 4. 推荐
related = requests.get(f"{BASE}/api/formulas/fma/related").json()["data"]["related"]
for r in related:
    print(r["id"], r["name_zh"])
```
