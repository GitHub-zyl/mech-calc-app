# 计算历史持久化 + 公式查询 API 实施计划

> **执行方式**: inline (用户在当前会话直接执行)
> **目标日期**: 2026-06-03
> **前置**: Phase 1 完成 (114 测试通过, 53% 覆盖率)

## 目标

1. 把整体测试覆盖率从 53% 提升到 ≥80% (重点: beam / strength / weld)
2. **P0**: SQLite 持久化 + REST 风格的 `/api/history` 接口
3. **P1**: 公式查询 API (F=ma 解析 + 详情 + 推荐)

## 总体架构

```
backend/
├── api/
│   ├── history.py           # P0 新增
│   ├── formulas.py          # P1 新增
│   └── calculations/
│       └── misc.py          # 注册新端点
├── database/
│   ├── __init__.py
│   ├── models.py            # P0 新增 (SQLite 表模型)
│   └── history_db.py        # P0 新增 (CRUD 操作)
├── calculations/
│   └── formulas_data.py     # P1 新增 (公式库)
└── tests/
    ├── unit/
    │   ├── test_calculations_beam.py   # 新增
    │   ├── test_calculations_strength.py # 新增
    │   ├── test_calculations_weld.py   # 新增
    │   ├── test_calculations_formulas.py # 新增
    │   └── test_history_db.py          # 新增
    └── integration/
        ├── test_api_history.py         # 新增
        └── test_api_formulas.py        # 新增
```

## 任务清单

### 阶段 0: 覆盖率提升 (前置)

#### Task 0.1: 编写 beam.py 单元测试
- **Files**: `tests/unit/test_calculations_beam.py` (新建)
- **目标**: beam.py 覆盖率 23% → 90%+
- **测试内容**:
  - `beam_section_inertia` 6 种截面 (circle/hollow_circle/rect/hollow_rect/i_beam/channel)
  - `calc_beam` 简支/悬臂/固支梁
  - 边界: 未知截面、空载、负长度

#### Task 0.2: 编写 strength.py 单元测试
- **Files**: `tests/unit/test_calculations_strength.py` (新建)
- **目标**: strength.py 覆盖率 29% → 80%+
- **测试内容**:
  - 压杆稳定 (欧拉公式 / 中长杆)
  - 键/销强度校核
  - 紧螺栓/松螺栓

#### Task 0.3: 编写 weld.py 单元测试
- **Files**: `tests/unit/test_calculations_weld.py` (新建)
- **目标**: weld.py 覆盖率 5% → 90%+
- **测试内容**:
  - 角焊缝 (tension/shear/combined)
  - 对接焊缝 (tension/bending/combined)
  - 错误参数 (缺 F/M)

### 阶段 1: P0 计算历史持久化

#### Task 1.1: 创建 SQLite 表结构
- **Files**: `backend/database/history_db.py` (新建)
- **Schema**:
  ```sql
  CREATE TABLE IF NOT EXISTS calc_history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts REAL NOT NULL,                  -- Unix timestamp
      category TEXT NOT NULL,            -- e.g. 'gear'
      endpoint TEXT NOT NULL,            -- e.g. '/api/calc/gear/spur'
      calc_id TEXT,                      -- 前端注册表 ID
      input_json TEXT NOT NULL,          -- 序列化的输入参数
      output_json TEXT NOT NULL,         -- 序列化的输出结果
      client_ip TEXT,                    -- 客户端 IP (可选)
      duration_ms REAL                   -- 计算耗时 ms
  );
  CREATE INDEX IF NOT EXISTS idx_calc_history_ts ON calc_history(ts DESC);
  CREATE INDEX IF NOT EXISTS idx_calc_history_cat ON calc_history(category);
  ```

#### Task 1.2: 实现 CRUD 模块
- **Files**: `backend/database/history_db.py`
- **Functions**:
  - `init_db(db_path)` - 初始化表
  - `add_record(...)` - 插入一条 (使用事务)
  - `list_records(limit, offset, category, since, until)` - 分页+筛选
  - `get_record(id)` - 详情
  - `delete_record(id)` - 删除
  - `count_records(category=None)` - 统计
  - `clear_all()` - 清空 (供测试)

#### Task 1.3: 实现 REST 蓝图
- **Files**: `backend/api/history.py` (新建)
- **Endpoints**:
  - `GET /api/history` - 列表 (支持 `?limit=&offset=&category=&since=&until=`)
  - `GET /api/history/<id>` - 详情
  - `POST /api/history` - 新增 (`{category, endpoint, calc_id, input, output, duration_ms}`)
  - `DELETE /api/history/<id>` - 删除
  - `GET /api/history/stats` - 统计 (总数, 按分类)
  - `DELETE /api/history` - 清空 (仅测试模式)

#### Task 1.4: 注册蓝图
- **Files**: `backend/app.py` (修改)
- **Content**: 注册 history_bp, 测试模式下使用临时 SQLite

#### Task 1.5: 集成测试
- **Files**: `tests/integration/test_api_history.py` (新建)
- **Test Cases**:
  - POST 成功插入
  - POST 验证 (缺 category/endpoint → 400)
  - GET 列表 (分页正确)
  - GET 详情
  - GET 按 category 筛选
  - DELETE 单条
  - 错误响应 (404 不存在的 ID)

#### Task 1.6: 单元测试
- **Files**: `tests/unit/test_history_db.py` (新建)
- **Test Cases**:
  - init_db 创建表
  - add_record + get_record 往返
  - list_records 分页
  - 事务回滚 (故意失败)
  - 索引存在性

### 阶段 2: P1 公式查询 API

#### Task 2.1: 公式库数据
- **Files**: `backend/calculations/formulas_data.py` (新建)
- **Content**: 30+ 常用机械工程公式
  - 力学: F=ma, F=μN, p=F/A
  - 强度: σ=F/A, τ=T/Wp
  - 圆周运动: a=v²/r, T=Jα
  - 振动: T=2π√(m/k)
  - 几何: A=πd²/4, V=πd²/4·L
  - 流体: Q=Av, p=ρgh
  - 热: Q=cmΔT
  - 功率: P=Tω, P=Fv
  - 等

每条记录:
```python
{
    'id': 'fma',
    'name_zh': '牛顿第二定律',
    'name_en': "Newton's Second Law",
    'formula': 'F = m·a',
    'variables': {'F': {'name': '合外力', 'unit': 'N'}, 'm': {'name': '质量', 'unit': 'kg'}, 'a': {'name': '加速度', 'unit': 'm/s²'}},
    'category': 'mechanics',
    'description': '物体加速度与所受合外力成正比...',
    'tags': ['力学', '动力学', '基础'],
    'related': ['fnet', 'pfa'],
    'reference': '理论力学(哈工大) §2',
}
```

#### Task 2.2: 公式解析器
- **Files**: `backend/calculations/formula_parser.py` (新建)
- **Functions**:
  - `parse_variables(formula_str)` - 提取变量名 (单字母)
  - `solve(formula_id, given)` - 已知 n-1 个变量, 求第 n 个
    - 例: `solve('fma', {'m': 10, 'a': 2})` → F=20
  - `normalize(formula_str)` - 标准化公式字符串 (去空格/特殊字符)

#### Task 2.3: 公式 API 蓝图
- **Files**: `backend/api/formulas.py` (新建)
- **Endpoints**:
  - `GET /api/formulas` - 列出所有公式 (支持 `?category=&q=`)
  - `GET /api/formulas/categories` - 分类清单
  - `GET /api/formulas/<id>` - 公式详情
  - `GET /api/formulas/<id>/related` - 相关公式推荐
  - `POST /api/formulas/<id>/solve` - 求解 (`{given: {var: value}}`)

#### Task 2.4: 注册蓝图
- **Files**: `backend/app.py` (修改)

#### Task 2.5: 单元测试
- **Files**: `tests/unit/test_calculations_formulas.py` (新建)
- **Test Cases**:
  - parse_variables 正确性
  - solve 单变量求解 (F=ma, p=ρgh, P=Fv)
  - 错误处理 (缺变量, 公式不存在)

#### Task 2.6: 集成测试
- **Files**: `tests/integration/test_api_formulas.py` (新建)
- **Test Cases**:
  - GET /api/formulas 全部
  - GET 分类筛选
  - GET 关键词搜索
  - GET /api/formulas/fma 详情
  - GET /api/formulas/fma/related
  - POST /api/formulas/fma/solve

### 阶段 3: 收尾

#### Task 3.1: 文档
- **Files**:
  - `docs/api-history.md` (新建) - /api/history 完整文档
  - `docs/api-formulas.md` (新建) - /api/formulas 完整文档
  - 更新 `docs/superpowers/plans/2026-06-03-phase1-architecture-refactor.md` 添加 Phase 2 进展

#### Task 3.2: 全量回归
- 运行 `pytest backend/tests --cov=backend` 验证
- 目标: 全部通过, 覆盖率 ≥ 80%
- 性能: 新 API 仍 < 1ms (test_client)

#### Task 3.3: smoke_test 扩展
- **Files**: `backend/smoke_test.py` (修改)
- 增加 history / formulas 端点冒烟

## 风险与回退

| 风险 | 缓解 |
|------|------|
| SQLite 写锁 | 启用 WAL 模式 |
| 历史无限增长 | 默认 limit=20, 提供 DELETE 清空 |
| 公式求解歧义 | 一次只解一个变量, 显式错误 |
| 测试临时文件 | 使用 `tmp_path` fixture |

## 完成标准

- [x] 114 + 新增测试全部通过 (实际 438, 含 1 skip)
- [x] 整体覆盖率 ≥ 80% (实际 80%)
- [x] /api/history 可用 (POST/GET/DELETE/stats/categories)
- [x] /api/formulas 可用 (list/categories/detail/related/solve)
- [x] 文档完整 (api-history.md + api-formulas.md)
- [x] 性能保持亚毫秒级 (test_client 实测 < 1ms)

---

## 实施记录 (2026-06-04)

### 实际产出

| 类型     | 文件                                                          | 说明                          |
| -------- | ------------------------------------------------------------- | ----------------------------- |
| 数据库   | `backend/database/history_db.py`                              | SQLite + WAL + 索引 + CRUD    |
| 数据库   | `backend/database/__init__.py`                                | 模块导出                      |
| API 蓝图 | `backend/api/history.py`                                      | 7 个端点 (含 stats/categories) |
| API 蓝图 | `backend/api/formulas.py`                                     | 5 个端点 (list/cat/detail/related/solve) |
| 公式数据 | `backend/calculations/formulas_data.py`                       | 30 条公式 + 6 个工具函数      |
| 测试     | `backend/tests/unit/test_history_db.py`                       | 21 用例                        |
| 测试     | `backend/tests/unit/test_calculations_formulas.py`            | 41 用例                        |
| 测试     | `backend/tests/integration/test_api_history.py`               | 27 用例                        |
| 测试     | `backend/tests/integration/test_api_formulas.py`              | 24 用例 + 1 skip              |
| 文档     | `docs/api-history.md`                                         | /api/history 完整文档         |
| 文档     | `docs/api-formulas.md`                                        | /api/formulas 完整文档        |
| 冒烟     | `backend/smoke_test.py`                                       | 新增 history + formulas 段    |
| 配置     | `backend/app.py`                                              | 注册 history_bp / formulas_bp |
| 配置     | `backend/calculations/formulas_data.py`                       | 修复 fma.related 中不存在的 impulse |

### 覆盖率 (终态)

```
TOTAL                                                       5478   1087    80%
438 passed, 1 skipped in 12.60s
```

关键模块:

| 模块                                  | 覆盖率 |
| ------------------------------------- | ------ |
| `backend/api/formulas.py`           | 100%   |
| `backend/api/history.py`            | 97%    |
| `backend/calculations/formulas_data.py` | 96% |
| `backend/database/history_db.py`    | 92%    |

### 已知限制 (写入复盘)

1. **solve 仅支持反解 LHS 变量**: 例如 `F=ma` 可求 F, 不可求 m/a
   - 改进方向: 集成 `sympy` 实现完全反解
2. **数据库清空无二次确认**: `DELETE /api/history?all=1` 立即清空
   - 改进方向: 引入 `confirm_token` 或 `dry-run` 参数
3. **公式静态加载**: 公式库需重启服务生效
   - 改进方向: 从 JSON 文件热加载
4. **无并发写锁测试**: 多人同时 POST 未做压力测试
   - 改进方向: locust 压测 + 锁竞争用例
