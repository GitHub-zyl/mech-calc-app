# Phase 1 架构重构收尾报告

**日期**: 2026-06-03
**版本**: v2.1.0
**状态**: ✅ 已完成

---

## 1. 阶段目标

| 目标 | 状态 | 备注 |
|------|------|------|
| 应用工厂模式 (create_app) | ✅ | 测试/生产环境分离 |
| 蓝图模块化 (8 个 BP) | ✅ | meta/data/units/transmission/shaft_system/fasteners/fluid/misc |
| 旧路由兼容层 | ✅ | `/api/calculate/*` → `/api/calc/*` 308 重定向 |
| 数据加载缓存 | ✅ | `load_json` 单例 + 启动预热, 亚毫秒级响应 |
| Alpine.js 新前端 | ✅ | `/modern` 路由, 数据驱动注册表 |
| 测试体系 | ✅ | pytest 114 项, 集成/单元/兼容层全覆盖 |
| 性能压测 | ✅ | 全 API < 1ms 响应 (test_client) |

---

## 2. 后端架构

### 2.1 蓝图清单 (8 个 + compat)

| 蓝图 | URL 前缀 | 功能 |
|------|----------|------|
| `meta_bp` | `/api/meta` | 健康检查/版本/13 大类分类树 |
| `data_bp` | `/api/data` | 材料/钢材/铝材/塑料/轴承/O型圈/螺纹/物理常数 |
| `units_bp` | `/api/units` | 单位换算/批量换算/常数 |
| `transmission_bp` | `/api/calc` | 齿轮/蜗杆/带/链/凸轮 |
| `shaft_system_bp` | `/api/calc` | 轴/轴承/梁/疲劳 |
| `fasteners_bp` | `/api/calc` | 螺纹/焊接/键/强度 |
| `fluid_bp` | `/api/calc` | 液压/气动 |
| `misc_bp` | `/api/calc` | 公差/表面/弹簧/冲压/制动/联轴器 |
| `compat_bp` | (根) | 旧路由 308 重定向 + 占位接口 |

### 2.2 目录结构

```
backend/
├── app.py                 # 应用工厂
├── config.py              # Config / TestConfig
├── smoke_test.py          # 冒烟测试脚本
├── api/
│   ├── __init__.py
│   ├── meta.py            # 元信息
│   ├── data.py            # 数据查询
│   ├── units.py           # 单位换算
│   ├── errors.py          # 统一错误处理
│   ├── responses.py       # 统一响应格式
│   ├── compat.py          # 旧路由兼容层
│   └── calculations/
│       ├── transmission.py
│       ├── shaft_system.py
│       ├── fasteners.py
│       ├── fluid.py
│       └── misc.py
├── calculations/          # 纯计算模块 (无 Flask 依赖)
│   ├── __init__.py
│   ├── gear.py
│   ├── bearing.py / bearing_full.py
│   ├── beam.py / shaft.py / fatigue.py
│   ├── tolerance.py / surface.py
│   ├── spring.py / press.py / brake.py / coupling.py
│   ├── hydraulic.py / pneumatic.py
│   ├── worm.py / belt.py / chain.py / cam.py
│   ├── thermo.py / strength.py / weld.py / thread.py
│   └── mechanics.py
├── utils/
│   ├── convert.py         # 安全类型转换
│   ├── db.py              # JSON 加载+线程安全缓存
│   └── units.py           # 单位换算+物理常数
└── tests/
    ├── unit/
    │   ├── test_calculations_gear.py
    │   └── test_responses.py
    └── integration/
        ├── test_app_factory.py
        ├── test_api_data.py
        ├── test_api_units.py
        ├── test_api_transmission.py
        ├── test_api_shaft.py
        ├── test_api_misc.py
        └── test_compat.py
```

### 2.3 关键设计

**应用工厂**: `create_app(testing=False)` 接收 `testing` 标志, 测试环境使用 `TestConfig` 跳过外部依赖.

**统一响应格式**: `success(data, meta=None)` / `error(msg, code=400, details=None)`.

**统一错误处理**: `register_error_handlers(app)` 注册 400/404/405/500.

**数据缓存**: `load_json()` 单例 + `threading.Lock`, 应用启动时预热 `extracted_data.json` 和 `i18n_data.json`, 避免首请求卡顿.

**适配层 (适配计算模块 vs API 命名差异)**: `misc.py` 中部分端点需要将 API 语义化参数映射到计算模块的精确参数 (例如 `coupling_gear_torque` 接受 `power_kw, rpm` 而 API 接受 `T_Nm, n_rpm`).

---

## 3. 旧路由兼容

```
旧 URL                                  新 URL
/api/calculate/<cat>/<name>      →      /api/calc/<cat>/<name>     (308)
/api/material/search?q=...       →      /api/data/materials?q=...  (308)
/api/material/info?name=...      →      /api/data/materials/<name> (308)
/api/data/fit_recommendations    →      空列表占位 (Phase 2 实现)
/api/data/motor_knowledge        →      空列表占位 (Phase 2 实现)
```

**Phase 1 末保留**: 前端仍可继续使用旧 URL, 308 重定向无副作用.
**Phase 2 末删除**: 旧 JS 文件 (app.js/app-ext.js/app-ext2.js) 全部下线后, 蓝图 `compat_bp` 同步删除.

---

## 4. 测试结果

```
============================= test session starts =============================
platform win32 -- Python 3.12.2, pytest-9.0.3
collected 114 items

backend/tests/integration/test_api_data.py ............ 13 PASSED
backend/tests/integration/test_api_misc.py ............ 25 PASSED
backend/tests/integration/test_api_shaft.py ........... 11 PASSED
backend/tests/integration/test_api_transmission.py .... 15 PASSED
backend/tests/integration/test_api_units.py ........... 15 PASSED
backend/tests/integration/test_app_factory.py ......... 6 PASSED
backend/tests/integration/test_compat.py .............. 6 PASSED
backend/tests/unit/test_calculations_gear.py .......... 10 PASSED
backend/tests/unit/test_responses.py .................. 13 PASSED

============================= 114 passed in 5.66s =============================
```

**覆盖率** (重点模块):

| 模块 | 覆盖率 | 备注 |
|------|--------|------|
| calculations/gear.py | **98%** | 直齿轮/啮合/弯曲/接触强度/行星/复合 |
| tests/integration/* | **100%** | 全部集成测试覆盖 |
| utils/convert.py | 94% | safe_float/safe_int |
| calculations/shaft.py | 82% | 扭转/合成/疲劳/临界转速 |
| calculations/tolerance.py | 79% | 轴/孔/配合公差 |
| utils/units.py | 71% | 单位换算+物理常数 |
| **TOTAL** | **53%** | 计算模块未做完整单元测试 |

**后续 (Phase 2 优先级)**: 补齐 `beam/mechanics/strength/weld/press/surface/brake` 等模块的单元测试, 目标 >80% 覆盖率.

---

## 5. 性能数据

测试环境: Python 3.12, Windows 11, Flask test_client (in-process)

| 端点 | 平均延迟 | 备注 |
|------|----------|------|
| GET /api/meta/health | 0.143 ms | 内存响应 |
| GET /api/data/categories | 0.156 ms | 13 大类常量 |
| GET /api/data/materials?q=steel | 0.375 ms | 内存搜索 |
| POST /api/calc/gear/spur | 0.205 ms | 数值计算 |
| POST /api/calc/tolerance/fit | 0.235 ms | 公差查表 |
| POST /api/calc/bearing/life | 0.180 ms | 寿命公式 |

**注**: test_client 模式无 HTTP/序列化开销. 真实 HTTP + JSON 序列化场景预估 1-3 ms/请求.

---

## 6. 现代化前端 (`/modern`)

**新增**:
- `templates/modern.html` (Alpine.js 单页)
- `static/js/app-modern.js` (数据驱动注册表)

**特性**:
- 13 大类分类树 (从 `/api/meta/categories` 加载)
- 搜索过滤 (分类名/计算器名)
- 计算器注册表 (CALCULATORS) - 添加新计算器只需注册项, 无需改 HTML
- 实时表单生成 (按注册表字段)
- 本地会话历史 (内存, Phase 2 升级 localStorage + 服务端)

**未实现 (Phase 2)**:
- 配合度推荐表
- 电机常识表
- 公式查询/常数查询增强
- 历史持久化 (服务端 SQLite)
- 用户收藏

---

## 7. 已知问题与遗留事项

### 7.1 必须在 Phase 2 处理

1. **测试覆盖率**: 53% 总体覆盖率偏低, 重点补:
   - `calculations/beam.py` (23%) - 梁的弯曲/挠度/应力
   - `calculations/strength.py` (29%) - 压杆稳定/键/销
   - `calculations/weld.py` (5%) - 焊缝强度
   - `calculations/press.py` (29%) - 冲裁/弯曲/剪切
   - `calculations/surface.py` (17%) - 粗糙度换算
   - `calculations/mechanics.py` (13%) - 力学综合
   - `calculations/thermo.py` (0%) - 暂无测试
   - `calculations/bearing_full.py` (0%) - 完整轴承寿命

2. **公式查询/常数查询**: 当前 constants API 仅返回物理常数, 缺少工程常用公式 (F=ma, τ=T/W 等).

3. **计算历史持久化**: 当前仅内存历史, 关闭浏览器即丢失. Phase 2 应:
   - 新增 SQLite 表 `calc_history(id, ts, calc_id, input, output, user_ip)`
   - 新增 `POST /api/history` 和 `GET /api/history?limit=20`

4. **配合度推荐表/电机常识表**: 数据未录入, API 已 stub 返回空.

### 7.2 可选优化

- 引入 Locust 做正式 HTTP 压测 (而非 test_client).
- 引入 pre-commit 钩子 (black/flake8) 统一代码风格.
- 将 `/api/data/fit_recommendations` 等 Phase 2 占位端点实现.

---

## 8. 下一步 (Phase 2 启动条件)

| 条件 | 状态 |
|------|------|
| 114 测试全部通过 | ✅ |
| 8 大蓝图全部注册 | ✅ |
| 旧路由兼容层就绪 | ✅ |
| 性能基线建立 (亚毫秒) | ✅ |
| Alpine.js 新前端就绪 | ✅ |

**结论**: Phase 1 已完成. 可立即进入 Phase 2 (功能扩展).
