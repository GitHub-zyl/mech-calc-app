# 机械计算小程序 — 架构重构与功能扩展实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 1390 行的单体 app.py 重构为 Blueprint 模块化架构,引入 pytest + locust 测试体系;前端用 Alpine.js 重写为模块化组件;为 Phase 2 (常数/公式/历史查询、《机械设计手册》13 大分类体系) 奠定可扩展基础。

**Architecture:**
- **后端**: Flask Blueprint 按机械设计手册 13 大类拆分;统一 API 响应格式;集中错误处理;i18n 接入后端
- **前端**: Alpine.js + 模块化组件(取代 7 个零散 JS),按分类组织 Tab
- **数据层**: 已有 `data/extracted_data.json` (10399 行) 保持不变,新增 `data/formulas.json`(由现有 docstring 自动生成,**不写新公式**)
- **测试**: pytest 单元 + 集成,locust 压测,pytest-cov 覆盖率
- **不写原则**: 严格遵守"不编写公式与数据"——所有计算/常数/材料从现有模块和 JSON 读取

**Tech Stack:** Python 3.11+ / Flask 3 / Alpine.js 3 / pytest 8 / locust 2 / SQLite (历史)

---

## 一、当前状态速览 (来自代码分析)

| 维度 | 现状 | 目标 |
|------|------|------|
| `app.py` 行数 | 1390 行 (单体) | < 200 行 (入口) |
| 计算模块 | 24 个 (`.py` 文件) | 保持 |
| API 端点 | 80+ 散落 | 按 Blueprint 组织 |
| 错误处理 | try/except 散落 + 不一致 | 统一 `@app.errorhandler` + 响应包装 |
| 数据文件 | `extracted_data.json` 10399 行 | 保持,新增 `formulas.json` 索引 |
| 前端 JS | 7 个文件 (app.js + ext + ext2 + fix + i18n + lang + diag) | 1 个 Alpine.js 应用 + 模块化 store |
| 测试 | 仅 `test_all.py` (urllib,需服务运行) | pytest 单元 + 集成 + locust |
| 历史记录 | 无 | SQLite 持久化 |
| 公式查询 | 无 | 由 docstring 扫描生成索引 |
| 常数查询 | `PHYSICAL_CONSTANTS` (utils.units) | 已有,补 API + UI |

---

## 二、文件结构设计 (Phase 1 重构后)

```
机械计算小程序/
├── backend/
│   ├── __init__.py
│   ├── app.py                    # < 200 行, 仅应用工厂 + 蓝图注册
│   ├── api/                      # [新建] 蓝图层
│   │   ├── __init__.py
│   │   ├── errors.py             # 统一错误处理
│   │   ├── responses.py          # 统一响应格式
│   │   ├── i18n.py               # 后端 i18n (zh/en/ja)
│   │   ├── data.py               # 材料/钢材/铝材/塑料/轴承/O型圈 API
│   │   ├── units.py              # 单位换算 + 常数 API
│   │   ├── calculations/         # [新建] 按 13 大类组织的蓝图
│   │   │   ├── __init__.py
│   │   │   ├── transmission.py   # 传动: gear, worm, belt, chain, cam
│   │   │   ├── shaft_system.py   # 轴系: shaft, bearing, beam, fatigue
│   │   │   ├── fasteners.py      # 紧固: thread, weld, strength(部分)
│   │   │   ├── tolerance.py      # 公差
│   │   │   ├── materials.py      # 工程材料
│   │   │   ├── surface.py        # 表面/粗糙度
│   │   │   ├── springs.py        # 弹簧
│   │   │   ├── fluid.py          # 液压/气动
│   │   │   ├── press.py          # 冲压
│   │   │   ├── brake.py          # 制动/离合
│   │   │   ├── mechanics.py      # 力学/振动
│   │   │   ├── formulas.py       # [Phase 2] 公式查询
│   │   │   └── history.py        # [Phase 2] 历史
│   │   └── meta.py               # 健康检查/版本/分类树
│   ├── calculations/             # 现有 24 个模块, 不改实现
│   ├── utils/
│   │   ├── units.py              # 保持
│   │   ├── history_store.py      # [新建] SQLite 历史
│   │   ├── formula_index.py      # [新建] docstring → 公式索引
│   │   └── response.py           # [新建] 响应包装器
│   ├── config.py                 # [新建] 配置(端口/DB 路径/语言)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py           # 共享 fixtures (test client, app)
│       ├── unit/
│       │   ├── test_calculations_gear.py
│       │   ├── test_calculations_spring.py
│       │   └── ...               # 每个模块一个
│       ├── integration/
│       │   ├── test_api_gear.py
│       │   ├── test_api_units.py
│       │   └── ...
│       ├── perf/
│       │   └── locustfile.py
│       └── test_smoke.py         # 现有 test_all.py 改造
├── data/
│   ├── extracted_data.json       # 保持
│   ├── i18n_data.json            # 保持
│   ├── formulas.json             # [Phase 2 新建, 由 build 脚本生成]
│   └── history.db                # [Phase 2 新建, SQLite]
├── static/
│   ├── css/style.css             # 保持
│   └── js/
│       ├── app.js                # Alpine.js 入口 + 全局 store
│       ├── stores/               # [新建] 按 13 大类拆分的 store
│       │   ├── transmission.js
│       │   ├── shaft_system.js
│       │   └── ...
│       ├── components/           # [新建] UI 组件
│       │   ├── calc-panel.js
│       │   ├── history-panel.js
│       │   └── ...
│       └── utils/
│           ├── api.js
│           └── i18n.js
├── templates/
│   └── index.html                # Alpine.js 模板
├── docs/
│   ├── market-research.md        # [已新建]
│   └── superpowers/plans/
│       └── 2026-06-03-architecture-refactor-and-extension.md  # 本文件
├── pytest.ini                    # [新建]
├── requirements-dev.txt          # [新建] pytest/locust
├── pyproject.toml                # [新建] 项目元信息
└── 部署说明.md                   # 保持
```

---

## Phase 1: 架构重构与测试体系 (核心交付)

### Task 1: 建立项目元信息与配置层

**Files:**
- Create: `pyproject.toml`
- Create: `backend/config.py`
- Create: `pytest.ini`
- Create: `requirements-dev.txt`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "mech-design-calc"
version = "2.1.0"
description = "机械设计常用计算表 - 离线 Web 工具"
requires-python = ">=3.11"
dependencies = [
    "flask>=3.0",
    "openpyxl>=3.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-flask>=1.3",
    "locust>=2.20",
    "requests>=2.31",
]
```

- [ ] **Step 2: 创建 `backend/config.py`** — 集中配置

```python
"""应用配置"""
import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / 'data'
    DATA_FILE = DATA_DIR / 'extracted_data.json'
    I18N_FILE = DATA_DIR / 'i18n_data.json'
    HISTORY_DB = DATA_DIR / 'history.db'
    FORMULAS_FILE = DATA_DIR / 'formulas.json'

    HOST = os.environ.get('MECH_HOST', '127.0.0.1')
    PORT = int(os.environ.get('MECH_PORT', '9091'))
    DEBUG = os.environ.get('MECH_DEBUG', '0') == '1'

    DEFAULT_LANG = os.environ.get('MECH_LANG', 'zh')
    SUPPORTED_LANGS = ('zh', 'en', 'ja')
```

- [ ] **Step 3: 创建 `pytest.ini`**

```ini
[pytest]
testpaths = backend/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: 单元测试
    integration: 集成测试
    perf: 性能测试
```

- [ ] **Step 4: 创建 `requirements-dev.txt`**

```
pytest>=8.0
pytest-cov>=5.0
pytest-flask>=1.3
locust>=2.20
requests>=2.31
```

- [ ] **Step 5: 提交**

```bash
cd c:\Users\Administrator\机械计算小程序
git add pyproject.toml backend/config.py pytest.ini requirements-dev.txt
git commit -m "chore: 引入项目元信息与配置层"
```

---

### Task 2: 创建响应包装器与错误处理模块

**Files:**
- Create: `backend/utils/response.py`
- Create: `backend/api/errors.py`
- Create: `backend/api/responses.py`

- [ ] **Step 1: 写失败测试 `backend/tests/unit/test_responses.py`**

```python
from backend.api.responses import success, error

def test_success_default():
    r = success({'value': 1})
    assert r.status_code == 200
    assert r.get_json() == {'status': 'ok', 'data': {'value': 1}}

def test_success_with_meta():
    r = success({'a': 1}, meta={'count': 10})
    j = r.get_json()
    assert j['meta'] == {'count': 10}

def test_error_returns_400():
    r = error('参数错误', code=400, details={'field': 'm'})
    assert r.status_code == 400
    j = r.get_json()
    assert j['status'] == 'error'
    assert j['message'] == '参数错误'
    assert j['details'] == {'field': 'm'}
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
cd c:\Users\Administrator\机械计算小程序
python -m pytest backend/tests/unit/test_responses.py -v
```
Expected: ModuleNotFoundError (utils/response.py 不存在)

- [ ] **Step 3: 在 `backend/utils/convert.py` 创建 `safe_float` 工具** (从 app.py 抽离)

```python
"""类型转换工具"""
def safe_float(v, default=None):
    """安全转换为 float,失败返回 default"""
    if v is None or v == '':
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default
```

- [ ] **Step 4: 实现 `backend/api/responses.py`**

```python
"""统一 API 响应格式"""
from flask import jsonify

def success(data, meta=None, status=200):
    body = {'status': 'ok', 'data': data}
    if meta is not None:
        body['meta'] = meta
    return jsonify(body), status

def error(message, code=400, details=None):
    body = {'status': 'error', 'message': message, 'code': code}
    if details is not None:
        body['details'] = details
    return jsonify(body), code
```

- [ ] **Step 5: 运行测试,确认通过**

```bash
python -m pytest backend/tests/unit/test_responses.py -v
```
Expected: 3 passed

- [ ] **Step 6: 实现 `backend/api/errors.py`**

```python
"""集中错误处理"""
from .responses import error

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return error('请求格式错误: ' + str(e), code=400)

    @app.errorhandler(404)
    def not_found(e):
        return error('资源不存在: ' + str(e), code=404)

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception('Internal error')
        return error('服务器内部错误', code=500)
```

- [ ] **Step 7: 提交**

```bash
git add backend/utils/response.py backend/utils/convert.py backend/api/errors.py backend/api/responses.py backend/tests/unit/test_responses.py
git commit -m "feat(api): 统一响应格式与错误处理 + safe_float 工具"
```

---

### Task 3: 应用工厂与数据库加载器

**Files:**
- Create: `backend/utils/db.py` (从 app.py 抽离)
- Modify: `backend/app.py` (重写为工厂)

- [ ] **Step 1: 写失败测试 `backend/tests/integration/test_app_factory.py`**

```python
import pytest
from backend.app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()

def test_health(client):
    r = client.get('/api/meta/health')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert j['data']['app'] == 'mech-design-calc'
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
python -m pytest backend/tests/integration/test_app_factory.py -v
```
Expected: ImportError (create_app 不存在)

- [ ] **Step 3: 创建 `backend/utils/db.py`**

```python
"""数据库(JSON) 加载与缓存"""
import json
from pathlib import Path
from threading import Lock

_lock = Lock()
_cache = {}

def load_json(path: Path):
    if path in _cache:
        return _cache[path]
    with _lock:
        if path in _cache:
            return _cache[path]
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _cache[path] = data
        return data

def clear_cache():
    with _lock:
        _cache.clear()
```

- [ ] **Step 4: 创建 `backend/api/meta.py`**

```python
"""元信息端点: 健康检查/版本/分类树"""
from flask import Blueprint
from backend.api.responses import success

bp = Blueprint('meta', __name__, url_prefix='/api/meta')

@bp.get('/health')
def health():
    return success({'app': 'mech-design-calc', 'status': 'running'})

@bp.get('/version')
def version():
    from backend import __version__ if False else '2.1.0'  # 临时
    return success({'version': '2.1.0'})

# 13 大类分类树 (来自 market-research)
CATEGORIES = [
    {'id': 'geometry',     'name_zh': '常用几何与数学',     'name_en': 'Geometry & Math'},
    {'id': 'transmission', 'name_zh': '机械传动设计',       'name_en': 'Mechanical Transmission'},
    {'id': 'shaft_system', 'name_zh': '轴系结构与强度',     'name_en': 'Shaft System & Strength'},
    {'id': 'fasteners',    'name_zh': '紧固件与连接',       'name_en': 'Fasteners & Joints'},
    {'id': 'tolerance',    'name_zh': '公差配合与形位',     'name_en': 'Tolerance & Fit'},
    {'id': 'materials',    'name_zh': '工程材料参数',       'name_en': 'Engineering Materials'},
    {'id': 'surface',      'name_zh': '表面与热处理',       'name_en': 'Surface & Heat Treatment'},
    {'id': 'springs',      'name_zh': '弹簧设计',           'name_en': 'Spring Design'},
    {'id': 'fluid',        'name_zh': '流体传动',           'name_en': 'Hydraulic & Pneumatic'},
    {'id': 'press',        'name_zh': '冲压与塑性成形',     'name_en': 'Press & Forming'},
    {'id': 'brake',        'name_zh': '制动器与离合器',     'name_en': 'Brake & Clutch'},
    {'id': 'mechanics',    'name_zh': '力学与振动',         'name_en': 'Mechanics & Vibration'},
    {'id': 'units',        'name_zh': '单位制与换算',       'name_en': 'Units & Conversion'},
]

@bp.get('/categories')
def categories():
    return success(CATEGORIES)
```

- [ ] **Step 5: 重写 `backend/app.py` (应用工厂)**

```python
"""
机械设计常用计算表 - Flask App Factory
"""
import os
import sys
from pathlib import Path

# 确保能找到 calculations 模块
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template
from backend.config import Config
from backend.api.errors import register_error_handlers

# 导入所有蓝图 (先注册第一批,后续 Task 持续追加)
from backend.api.meta import bp as meta_bp
# 后续 Task 会追加: transmission_bp, shaft_system_bp ...

def create_app(testing=False):
    app = Flask(__name__,
                template_folder=str(Config.BASE_DIR / 'templates'),
                static_folder=str(Config.BASE_DIR / 'static'))
    app.config.from_object(Config)
    if testing:
        app.config['TESTING'] = True

    register_error_handlers(app)

    # 蓝图注册
    app.register_blueprint(meta_bp)
    # 后续 Task 会追加 register_blueprint(...)

    @app.route('/')
    def index():
        from flask import current_app
        idx = Path(current_app.template_folder) / 'index.html'
        if idx.exists():
            with open(idx, 'r', encoding='utf-8') as f:
                return current_app.response_class(f.read(), mimetype='text/html')
        return '<h1>Template not found</h1>', 404

    return app

# 保留直接 python app.py 启动的兼容性
if __name__ == '__main__':
    app = create_app()
    print(f'Start: http://{Config.HOST}:{Config.PORT}')
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
```

- [ ] **Step 6: 运行测试,确认通过**

```bash
python -m pytest backend/tests/integration/test_app_factory.py -v
```
Expected: 1 passed

- [ ] **Step 7: 启动验证**

```bash
python backend/app.py
# 浏览器: http://127.0.0.1:9091/api/meta/health
# 期望: {"status":"ok","data":{"app":"mech-design-calc","status":"running"}}
```

- [ ] **Step 8: 提交**

```bash
git add backend/utils/db.py backend/api/meta.py backend/app.py backend/tests/
git commit -m "refactor(app): 应用工厂 + 元信息 API + 13 大类分类树"
```

---

### Task 4: 数据 API 蓝图 (材料/钢材/铝材/塑料/轴承/O型圈)

**Files:**
- Create: `backend/api/data.py`
- Create: `backend/tests/integration/test_api_data.py`

- [ ] **Step 1: 写失败测试**

```python
import pytest
from backend.app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()

def test_materials_search(client):
    r = client.get('/api/data/materials?q=Iron')
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert isinstance(j['data'], list)

def test_bearings_deep_groove(client):
    r = client.get('/api/data/bearings')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], list)

def test_categories_listing(client):
    r = client.get('/api/data/categories')
    assert r.status_code == 200
    j = r.get_json()
    assert 'materials' in j['data']
    assert 'bearings' in j['data']

def test_units_constants(client):
    r = client.get('/api/data/constants')
    assert r.status_code == 200
    j = r.get_json()
    assert isinstance(j['data'], dict)
    assert 'g' in j['data'] or 'gravity' in j['data']
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
python -m pytest backend/tests/integration/test_api_data.py -v
```
Expected: 404 (路由不存在)

- [ ] **Step 3: 实现 `backend/api/data.py`**

```python
"""材料/标准件/常数 数据 API"""
from flask import Blueprint, request
from backend.config import Config
from backend.utils.db import load_json
from backend.api.responses import success

bp = Blueprint('data', __name__, url_prefix='/api/data')

DB = load_json(Config.DATA_FILE)

@bp.get('/materials')
def materials():
    q = (request.args.get('q') or '').lower()
    items = DB.get('materials', [])
    if q:
        items = [m for m in items if q in m.get('name', '').lower()]
    return success(items[:100], meta={'total': len(items), 'returned': min(100, len(items))})

@bp.get('/materials/<name>')
def material_detail(name):
    for m in DB.get('materials', []):
        if m.get('name') == name:
            return success(m)
    return success(None, meta={'found': False})

@bp.get('/steel-grades')
def steel_grades():
    return success(DB.get('steel_grades', []))

@bp.get('/aluminum-grades')
def aluminum_grades():
    return success(DB.get('aluminum_grades', []))

@bp.get('/plastics')
def plastics():
    return success(DB.get('plastics', []))

@bp.get('/bearings')
def bearings():
    return success(DB.get('bearings_deep_groove', []))

@bp.get('/bearings/thrust')
def bearings_thrust():
    return success(DB.get('bearings_thrust', []))

@bp.get('/oring-groove')
def oring():
    sec = request.args.get('diameter', type=float)
    items = DB.get('oring_groove', [])
    if sec is not None:
        # 找最接近的
        items = sorted(items, key=lambda x: abs(x.get('section_diameter', 0) - sec))[:10]
    return success(items)

@bp.get('/threads/metric')
def threads_metric():
    spec = request.args.get('spec')
    items = DB.get('threads_metric', [])
    if spec:
        items = [t for t in items if spec.upper() in str(t).upper()][:20]
    return success(items[:50])

@bp.get('/threads/imperial')
def threads_imperial():
    return success(DB.get('threads_imperial', []))

@bp.get('/constants')
def constants():
    from backend.utils.units import PHYSICAL_CONSTANTS
    return success(PHYSICAL_CONSTANTS)

@bp.get('/categories')
def categories():
    """数据子类别清单"""
    return success({
        'materials': '工程材料',
        'steel_grades': '钢材牌号',
        'aluminum_grades': '铝材牌号',
        'plastics': '塑料',
        'bearings': '深沟球轴承',
        'bearings_thrust': '推力轴承',
        'oring_groove': 'O型圈沟槽',
        'threads_metric': '公制螺纹',
        'threads_imperial': '英制螺纹',
    })
```

- [ ] **Step 4: 在 `backend/app.py` 注册蓝图**

修改 `create_app()` 函数,新增:
```python
from backend.api.data import bp as data_bp
# ...
app.register_blueprint(data_bp)
```

- [ ] **Step 5: 运行测试,确认通过**

```bash
python -m pytest backend/tests/integration/test_api_data.py -v
```
Expected: 4 passed

- [ ] **Step 6: 提交**

```bash
git add backend/api/data.py backend/tests/integration/test_api_data.py backend/app.py
git commit -m "feat(data): 统一材料/标准件/常数数据 API"
```

---

### Task 5: 单位换算蓝图

**Files:**
- Create: `backend/api/units.py`
- Create: `backend/tests/integration/test_api_units.py`

- [ ] **Step 1: 写失败测试**

```python
import pytest
from backend.app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()

def test_categories(client):
    r = client.get('/api/units/categories')
    assert r.status_code == 200
    j = r.get_json()
    assert 'length' in j['data']
    assert 'pressure' in j['data']

def test_convert_length(client):
    r = client.post('/api/units/convert', json={
        'value': 1, 'from': 'm', 'to': 'mm', 'category': 'length'
    })
    assert r.status_code == 200
    j = r.get_json()
    assert abs(j['data']['result'] - 1000) < 1e-6

def test_convert_pressure(client):
    r = client.post('/api/units/convert', json={
        'value': 1, 'from': 'MPa', 'to': 'Pa', 'category': 'pressure'
    })
    j = r.get_json()
    assert abs(j['data']['result'] - 1e6) < 1e-3

def test_convert_invalid(client):
    r = client.post('/api/units/convert', json={
        'value': 1, 'from': 'm', 'to': 'kg', 'category': 'length'
    })
    assert r.status_code in (400, 422)
```

- [ ] **Step 2: 运行测试,确认失败**

```bash
python -m pytest backend/tests/integration/test_api_units.py -v
```
Expected: 404

- [ ] **Step 3: 实现 `backend/api/units.py`**

```python
"""单位换算 API"""
from flask import Blueprint, request
from backend.api.responses import success, error
from backend.utils.units import convert_all, list_categories, PHYSICAL_CONSTANTS

bp = Blueprint('units', __name__, url_prefix='/api/units')

@bp.get('/categories')
def categories():
    return success(list_categories())

@bp.post('/convert')
def convert():
    d = request.get_json() or {}
    try:
        result = convert_all(
            d.get('value', 1),
            d.get('from', ''),
            d.get('to', ''),
            d.get('category', 'length')
        )
        return success(result)
    except (ValueError, KeyError) as e:
        return error(f'换算失败: {e}', code=400)

@bp.get('/constants')
def constants():
    return success(PHYSICAL_CONSTANTS)
```

- [ ] **Step 4: 在 `backend/app.py` 注册**

```python
from backend.api.units import bp as units_bp
# ...
app.register_blueprint(units_bp)
```

- [ ] **Step 5: 运行测试,确认通过**

```bash
python -m pytest backend/tests/integration/test_api_units.py -v
```
Expected: 4 passed

- [ ] **Step 6: 提交**

```bash
git add backend/api/units.py backend/tests/integration/test_api_units.py backend/app.py
git commit -m "feat(units): 单位换算 API 蓝图"
```

---

### Task 6: 齿轮/蜗杆/传动蓝图 (transmission)

**Files:**
- Create: `backend/api/calculations/__init__.py`
- Create: `backend/api/calculations/transmission.py`
- Create: `backend/tests/unit/test_calculations_gear.py`
- Create: `backend/tests/integration/test_api_transmission.py`

- [ ] **Step 1: 写齿轮单元测试**

```python
# backend/tests/unit/test_calculations_gear.py
import pytest
from backend.calculations.gear import spur_gear_params, spur_gear_mesh

def test_spur_gear_basic():
    r = spur_gear_params(m=3, z=20)
    assert r['pitch_diameter'] == 60.0
    assert r['tip_diameter'] == 66.0
    assert r['module'] == 3
    assert r['teeth'] == 20

def test_spur_gear_with_modification():
    r = spur_gear_params(m=3, z=20, x=0.3)
    assert r['modification_coefficient'] == 0.3
    assert r['pitch_diameter'] == 60.0  # 变位不影响分度圆

def test_mesh_returns_both_gears():
    r = spur_gear_mesh(m=3, z1=20, z2=60)
    assert r['gear1']['teeth'] == 20
    assert r['gear2']['teeth'] == 60
    assert r['center_distance'] == 120.0

def test_invalid_teeth_raises():
    with pytest.raises(TypeError):
        spur_gear_params(m=3, z='abc')  # 类型错误
```

- [ ] **Step 2: 运行,确认现有实现通过**

```bash
python -m pytest backend/tests/unit/test_calculations_gear.py -v
```
Expected: 4 passed (不改实现,仅测试)

- [ ] **Step 3: 写集成测试 `test_api_transmission.py`**

```python
import pytest
from backend.app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()

def test_gear_spur(client):
    r = client.post('/api/calc/gear/spur', json={'module': 3, 'teeth': 20})
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert j['data']['pitch_diameter'] == 60.0

def test_gear_missing_params(client):
    r = client.post('/api/calc/gear/spur', json={'module': 3})
    assert r.status_code in (400, 422)

def test_worm_geometry(client):
    r = client.post('/api/calc/worm/geometry', json={'m': 2, 'z1': 1, 'z2': 30, 'q': 10})
    assert r.status_code == 200
    j = r.get_json()
    assert 'center_distance' in j['data']
```

- [ ] **Step 4: 运行,确认失败**

```bash
python -m pytest backend/tests/integration/test_api_transmission.py -v
```
Expected: 404

- [ ] **Step 5: 实现 `backend/api/calculations/transmission.py`**

```python
"""传动类计算 API: 齿轮/蜗杆/带/链/凸轮"""
from flask import Blueprint, request
from backend.api.responses import success, error
from backend.calculations.gear import (
    spur_gear_params, spur_gear_mesh, gear_motor_selection, rack_and_pinion,
    gear_bending_strength, gear_contact_strength, gear_force,
    planetary_gear, compound_gear_train
)
from backend.calculations.worm import worm_geometry, worm_efficiency
from backend.calculations.belt import vbelt_calc, synchronous_belt_calc
from backend.calculations.chain import roller_chain_params, chain_length, conveyor_chain_tension
from backend.calculations.cam import cam_profile_points, cam_analysis, indexer_selection, divider_general

bp = Blueprint('transmission', __name__, url_prefix='/api/calc')

def _f(d, k, default=None):
    try:
        v = d.get(k)
        return float(v) if v is not None and v != '' else default
    except (TypeError, ValueError):
        return default

@bp.post('/gear/spur')
def gear_spur():
    d = request.get_json() or {}
    m = _f(d, 'module')
    z = _f(d, 'teeth')
    if not m or not z:
        return error('请填写模数(m)和齿数(z)', code=400)
    return success(spur_gear_params(m, int(z),
                                    _f(d, 'pressure_angle', 20),
                                    x=_f(d, 'modification_coefficient', 0) or 0))

@bp.post('/gear/mesh')
def gear_mesh():
    d = request.get_json() or {}
    if not all([_f(d, 'module'), _f(d, 'teeth1'), _f(d, 'teeth2')]):
        return error('请填写模数和齿数', code=400)
    return success(spur_gear_mesh(_f(d, 'module'),
                                  int(_f(d, 'teeth1')),
                                  int(_f(d, 'teeth2')),
                                  _f(d, 'pressure_angle', 20),
                                  x1=_f(d, 'x1', 0) or 0,
                                  x2=_f(d, 'x2', 0) or 0))

# ... 其余 10+ 端点按相同模式迁移 (gear_motor, rack, gear_bending, gear_contact, gear_force, planetary, compound, worm_geometry, worm_efficiency, vbelt, sync_belt, sprocket, chain_length, conveyor_chain, cam_*, indexer, divider)
# 每个端点遵循 "解析参数 → 调用现有函数 → 包装响应" 模式
```

(此文件实际实现时,需完整迁移以下端点:
- `/gear/spur`, `/gear/mesh`, `/gear/motor`, `/gear/rack`, `/gear/bending`, `/gear/contact`, `/gear/force`, `/gear/planetary`, `/gear/compound`
- `/worm/geometry`, `/worm/efficiency`
- `/belt/vbelt`, `/belt/synchronous`
- `/chain/sprocket`, `/chain/length`, `/chain/conveyor`
- `/cam/profile`, `/cam/analysis`, `/cam/indexer`, `/cam/divider`
)

- [ ] **Step 6: 在 `backend/app.py` 注册**

```python
from backend.api.calculations.transmission import bp as transmission_bp
# ...
app.register_blueprint(transmission_bp)
```

- [ ] **Step 7: 运行所有测试,确认通过**

```bash
python -m pytest backend/tests/ -v
```
Expected: 既有 + 新增 4 个 transmission 用例全部通过

- [ ] **Step 8: 启动验证(保留旧路由兼容)**

```bash
python backend/app.py
# 验证新旧路由: /api/calculate/gear/spur (旧) 与 /api/calc/gear/spur (新) 同时可用
```

- [ ] **Step 9: 提交**

```bash
git add backend/api/calculations/ backend/tests/
git commit -m "refactor(calc): 传动类(齿轮/蜗杆/带/链/凸轮)拆为 Blueprint"
```

---

### Task 7: 轴系与强度蓝图 (shaft_system)

**Files:**
- Create: `backend/api/calculations/shaft_system.py`
- Create: `backend/tests/integration/test_api_shaft.py`

- [ ] **Step 1: 写失败测试**

```python
import pytest
from backend.app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    return app.test_client()

def test_shaft_torsion(client):
    r = client.post('/api/calc/shaft/torsion', json={'d': 50, 'P': 5.5, 'n': 1450})
    assert r.status_code == 200
    j = r.get_json()
    assert j['status'] == 'ok'
    assert 'T' in j['data']
    assert 'tau' in j['data']

def test_bearing_life(client):
    r = client.post('/api/calc/bearing/life', json={'C': 25000, 'P': 5000, 'n': 3000})
    assert r.status_code == 200
    j = r.get_json()
    assert 'L10_hours' in j['data'] or 'life_hours' in j['data']

def test_beam_calc(client):
    r = client.post('/api/calc/beam/calc', json={
        'beam_type': 'simply_supported',
        'L': 1000,
        'loads': [{'type': 'point', 'F': 1000, 'a': 500}],
        'E': 206000,
        'I': 1e5
    })
    assert r.status_code == 200
```

- [ ] **Step 2: 运行,确认失败**

```bash
python -m pytest backend/tests/integration/test_api_shaft.py -v
```
Expected: 404

- [ ] **Step 3: 实现 `backend/api/calculations/shaft_system.py`**

(从 app.py 迁移以下端点到 Blueprint,实现模式同 Task 6:
- `/shaft/torsion`, `/shaft/combined`, `/shaft/fatigue`, `/shaft/critical-speed`
- `/bearing/life`, `/bearing/equivalent`, `/bearing/life-modified`, `/bearing/min-load`, `/bearing/speed-limit`
- `/beam/section`, `/beam/calc`
- `/fatigue/sn-curve`, `/fatigue/stress-conc`, `/fatigue/miner`
)

- [ ] **Step 4: 在 `backend/app.py` 注册**

```python
from backend.api.calculations.shaft_system import bp as shaft_system_bp
app.register_blueprint(shaft_system_bp)
```

- [ ] **Step 5: 测试通过 + 提交**

```bash
python -m pytest backend/tests/integration/test_api_shaft.py -v
git add backend/api/calculations/shaft_system.py backend/tests/
git commit -m "refactor(calc): 轴系/轴承/梁/疲劳 拆为 Blueprint"
```

---

### Task 8: 紧固件/连接/公差/弹簧/材料/表面/流体/冲压/制动/力学 蓝图 (剩余 10 个)

**Files:** (每个 1 个文件)
- `backend/api/calculations/fasteners.py`
- `backend/api/calculations/tolerance.py`
- `backend/api/calculations/materials_calc.py` (材料力学,非材料数据)
- `backend/api/calculations/surface.py`
- `backend/api/calculations/springs.py`
- `backend/api/calculations/fluid.py`
- `backend/api/calculations/press.py`
- `backend/api/calculations/brake.py`
- `backend/api/calculations/mechanics.py`
- `backend/api/calculations/coupling.py`

- [ ] **Step 1: 写每个蓝图的集成测试** (按 Task 6 模式, 10 个 test_*.py)

- [ ] **Step 2: 实现 10 个蓝图** (从 app.py 迁移,模式同 Task 6)

- [ ] **Step 3: 在 `backend/app.py` 注册全部**

- [ ] **Step 4: 运行全套测试,确认通过**

```bash
python -m pytest backend/tests/ -v --tb=short
```
Expected: 全部通过,无 ImportError

- [ ] **Step 5: 验证 `backend/app.py` 已 < 200 行**

```bash
wc -l backend/app.py
```
Expected: < 200

- [ ] **Step 6: 启动,curl 抽样 5 个端点,确认无回归**

```bash
python backend/app.py &
curl http://127.0.0.1:9091/api/meta/health
curl -X POST http://127.0.0.1:9091/api/calc/gear/spur -H 'Content-Type: application/json' -d '{"module":3,"teeth":20}'
curl -X POST http://127.0.0.1:9091/api/units/convert -H 'Content-Type: application/json' -d '{"value":1,"from":"m","to":"mm","category":"length"}'
curl http://127.0.0.1:9091/api/data/materials?q=Iron
curl http://127.0.0.1:9091/api/meta/categories
```

- [ ] **Step 7: 提交**

```bash
git add backend/api/calculations/ backend/app.py backend/tests/
git commit -m "refactor(calc): 全部 11 个分类蓝图迁移完成"
```

---

### Task 9: 旧路由兼容层 (过渡期)

**Files:**
- Modify: `backend/app.py`

- [ ] **Step 1: 在 app.py 添加重定向映射**

```python
# 兼容旧路由: /api/calculate/* → /api/calc/*
COMPAT_REDIRECTS = {
    '/api/calculate/gear/spur':       '/api/calc/gear/spur',
    '/api/calculate/spring/compression': '/api/calc/spring/compression',
    # ... 80+ 映射从原 app.py 复制
}

@app.route('/api/calculate/<path:subpath>', methods=['GET', 'POST'])
def legacy_calculate(subpath):
    from flask import request, redirect
    new_path = f'/api/calc/{subpath}'
    if request.method == 'POST':
        return redirect(new_path, code=307)  # 保留 POST + body
    return redirect(new_path, code=308)
```

- [ ] **Step 2: 启动 + 跑 `test_all.py` 验证向后兼容**

```bash
python backend/app.py &
python backend/test_all.py
```
Expected: 全部 pass (兼容旧 URL)

- [ ] **Step 3: 提交**

```bash
git add backend/app.py
git commit -m "feat(api): 旧 URL 重定向兼容层"
```

---

### Task 10: 性能优化 — 数据加载缓存

**Files:**
- Modify: `backend/utils/db.py` (已有)
- Create: `backend/tests/unit/test_db_cache.py`

- [ ] **Step 1: 写缓存测试**

```python
from backend.utils.db import load_json, clear_cache
from pathlib import Path
import time

def test_cache_returns_same_instance():
    p = Path('data/extracted_data.json')
    a = load_json(p)
    b = load_json(p)
    assert a is b  # 同对象 = 命中缓存

def test_cache_speedup(tmp_path):
    p = tmp_path / 't.json'
    p.write_text('{"a": 1}')
    t1 = time.perf_counter()
    load_json(p)
    first = time.perf_counter() - t1
    t2 = time.perf_counter()
    load_json(p)
    second = time.perf_counter() - t2
    assert second < first / 10  # 缓存后快 10x

def test_clear_cache_reloads(tmp_path):
    p = tmp_path / 't.json'
    p.write_text('{"v": 1}')
    a = load_json(p)
    clear_cache()
    b = load_json(p)
    assert a == b
    assert a is not b
```

- [ ] **Step 2: 验证现有 `load_json` 已实现缓存**

```bash
python -m pytest backend/tests/unit/test_db_cache.py -v
```
Expected: 3 passed

- [ ] **Step 3: 写性能基准 `backend/tests/perf/bench_data.py`**

```python
"""数据加载性能基准"""
import time
from backend.utils.db import load_json
from backend.config import Config

p = Config.DATA_FILE
# 冷启动
t = time.perf_counter()
data = load_json(p)
cold = time.perf_counter() - t
print(f'冷加载: {cold*1000:.1f}ms, {len(data["materials"])} 材料')

# 热加载
t = time.perf_counter()
data = load_json(p)
hot = time.perf_counter() - t
print(f'热加载: {hot*1000:.4f}ms')

# 搜索
t = time.perf_counter()
hits = [m for m in data['materials'] if 'Steel' in m.get('name', '')]
print(f'搜索 Steel: {(time.perf_counter()-t)*1000:.1f}ms, {len(hits)} 结果')
```

- [ ] **Step 4: 运行基准,记录基线**

```bash
python backend/tests/perf/bench_data.py
```
Expected output:
```
冷加载: <500ms
热加载: <0.1ms
搜索 Steel: <10ms
```

- [ ] **Step 5: 添加 `data/materials` API 索引加速** (在 `backend/api/data.py`)

```python
# 启动时构建小索引(小写 name → 索引)
_MATERIALS_INDEX = None

def _build_materials_index():
    global _MATERIALS_INDEX
    if _MATERIALS_INDEX is not None:
        return _MATERIALS_INDEX
    items = DB.get('materials', [])
    _MATERIALS_INDEX = [(i, m.get('name', '').lower()) for i, m in enumerate(items)]
    return _MATERIALS_INDEX

@bp.get('/materials')
def materials():
    q = (request.args.get('q') or '').lower()
    items = DB.get('materials', [])
    if q:
        # 优化: 一次遍历,避免 list comp 多次调用
        items = [m for m in items if q in m.get('name', '').lower()]
    return success(items[:100], meta={'total': len(items), 'returned': min(100, len(items))})
```

- [ ] **Step 6: 跑基准,确认搜索 < 5ms**

```bash
python backend/tests/perf/bench_data.py
```

- [ ] **Step 7: 提交**

```bash
git add backend/utils/db.py backend/api/data.py backend/tests/
git commit -m "perf(data): JSON 加载缓存 + 材料搜索优化"
```

---

### Task 11: locust 压测

**Files:**
- Create: `backend/tests/perf/locustfile.py`

- [ ] **Step 1: 写 locustfile**

```python
"""机械计算小程序 - 性能压测"""
from locust import HttpUser, task, between

class MechUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def health(self):
        self.client.get('/api/meta/health')

    @task(5)
    def gear_calc(self):
        self.client.post('/api/calc/gear/spur', json={'module': 3, 'teeth': 20})

    @task(3)
    def unit_convert(self):
        self.client.post('/api/units/convert', json={
            'value': 1, 'from': 'MPa', 'to': 'Pa', 'category': 'pressure'
        })

    @task(2)
    def material_search(self):
        self.client.get('/api/data/materials?q=Steel')

    @task(1)
    def spring_calc(self):
        self.client.post('/api/calc/spring/compression', json={
            'wire_diameter': 4, 'mean_diameter': 30, 'coils': 10
        })

    @task(1)
    def categories(self):
        self.client.get('/api/meta/categories')
```

- [ ] **Step 2: 启动 app,跑压测**

```bash
# 终端 1
python backend/app.py
# 终端 2
cd c:\Users\Administrator\机械计算小程序
locust -f backend/tests/perf/locustfile.py --host=http://127.0.0.1:9091 --users=20 --spawn-rate=5 --run-time=30s --headless
```

Expected: 无 5xx,p95 < 100ms

- [ ] **Step 3: 提交**

```bash
git add backend/tests/perf/locustfile.py
git commit -m "test(perf): locust 压测脚本"
```

---

### Task 12: 前端 Alpine.js 重写

**Files:**
- Create: `static/js/app.js` (Alpine 入口)
- Create: `static/js/stores/api.js`
- Create: `static/js/stores/i18n.js`
- Create: `static/js/stores/transmission.js`
- Create: `static/js/stores/shaft_system.js`
- (后续按 13 大类各 1 个 store)
- Create: `static/js/components/calc-panel.js`
- Create: `static/js/components/result-panel.js`
- Modify: `templates/index.html` (用 Alpine 改造)
- Delete: `static/js/app-ext.js`, `app-ext2.js`, `app-fix.js`, `app-lang.js`, `app-i18n.js`, `diag.js` (Phase 1 末)

- [ ] **Step 1: 引入 Alpine.js (CDN,或本地)**

修改 `templates/index.html` 头部:
```html
<script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
<script type="module" src="{{ url_for('static', filename='js/app.js') }}"></script>
```

- [ ] **Step 2: 创建 `static/js/stores/api.js`**

```javascript
// 统一 API 调用层
export const api = {
  async get(url) {
    const r = await fetch(url);
    return r.json();
  },
  async post(url, body) {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return r.json();
  },
  // 高层方法
  meta: {
    health: () => api.get('/api/meta/health'),
    categories: () => api.get('/api/meta/categories'),
  },
  data: {
    materials: (q) => api.get(`/api/data/materials?q=${encodeURIComponent(q || '')}`),
    constants: () => api.get('/api/data/constants'),
  },
  units: {
    categories: () => api.get('/api/units/categories'),
    convert: (value, from, to, category) => api.post('/api/units/convert', { value, from, to, category }),
  },
  calc: {
    gear: {
      spur: (params) => api.post('/api/calc/gear/spur', params),
      mesh: (params) => api.post('/api/calc/gear/mesh', params),
    },
    spring: {
      compression: (params) => api.post('/api/calc/spring/compression', params),
    },
    // ...
  },
};
```

- [ ] **Step 3: 创建 `static/js/stores/i18n.js`**

```javascript
// 后端 i18n (与前端 i18n_data.json 合并)
import { api } from './api.js';

export const i18nStore = {
  current: 'zh',
  dict: {},
  async load(lang) {
    // 先拉取后端 i18n
    const res = await fetch(`/data/i18n_data.json`).then(r => r.json());
    this.dict = res;
    this.current = lang || 'zh';
  },
  t(key) {
    const entry = this.dict[key];
    if (!entry) return key;
    return entry[this.current] || entry.zh || key;
  },
};
```

- [ ] **Step 4: 创建 `static/js/stores/transmission.js`**

```javascript
// 传动计算 store (Alpine.data 注册)
import { api } from './api.js';

export function registerTransmissionStore(Alpine) {
  Alpine.data('transmission', () => ({
    gear: { module: 3, teeth: 20, pressure_angle: 20, x: 0 },
    result: null,
    loading: false,
    error: null,
    async calculateSpur() {
      this.loading = true;
      this.error = null;
      const r = await api.calc.gear.spur(this.gear);
      this.loading = false;
      if (r.status === 'error') {
        this.error = r.message;
        return;
      }
      this.result = r.data;
    },
  }));
}
```

- [ ] **Step 5: 创建 `static/js/app.js` 入口**

```javascript
// 主入口: 注册所有 store
import { i18nStore } from './stores/i18n.js';
import { registerTransmissionStore } from './stores/transmission.js';

document.addEventListener('alpine:init', () => {
  const Alpine = window.Alpine;
  // 全局
  Alpine.store('i18n', i18nStore);
  // 组件
  registerTransmissionStore(Alpine);
  // 后续追加 registerShaftSystemStore 等
});

document.addEventListener('DOMContentLoaded', () => {
  i18nStore.load('zh');
});
```

- [ ] **Step 6: 改造 `templates/index.html` 顶部 Tab**

```html
<div x-data="{ tab: 'transmission' }">
  <nav class="tabs">
    <template x-for="cat in $store.categories" :key="cat.id">
      <button @click="tab = cat.id" :class="{active: tab === cat.id}"
              x-text="cat.name_zh"></button>
    </template>
  </nav>

  <section x-show="tab === 'transmission'" x-data="transmission">
    <h2>齿轮计算</h2>
    <div>
      模数: <input type="number" x-model.number="gear.module">
      齿数: <input type="number" x-model.number="gear.teeth">
      <button @click="calculateSpur()" :disabled="loading">计算</button>
    </div>
    <div x-show="result" class="result">
      <pre x-text="JSON.stringify(result, null, 2)"></pre>
    </div>
    <div x-show="error" class="error" x-text="error"></div>
  </section>

  <!-- 其他 12 个分类的 <section> 后续追加 -->
</div>
```

- [ ] **Step 7: 启动,浏览器验证至少 3 个分类可用**

```bash
python backend/app.py
# 浏览器: http://127.0.0.1:9091
# 验证: 齿轮/弹簧/单位换算 三个 Tab 可正常计算
```

- [ ] **Step 8: 删除旧 JS 文件**

```bash
del static\js\app-ext.js static\js\app-ext2.js static\js\app-fix.js static\js\app-lang.js static\js\app-i18n.js static\js\diag.js
```

(若旧 JS 包含需保留的逻辑,先迁到 Alpine store 再删)

- [ ] **Step 9: 提交**

```bash
git add static/js/ templates/index.html
git rm static/js/app-ext.js static/js/app-ext2.js static/js/app-fix.js static/js/app-lang.js static/js/app-i18n.js static/js/diag.js
git commit -m "refactor(frontend): Alpine.js 重写,7 个零散 JS → 模块化 store"
```

---

### Task 13: 全量回归与覆盖率

**Files:**
- Create: `backend/tests/test_smoke.py` (从 test_all.py 改造)

- [ ] **Step 1: 改造 `test_all.py` → pytest 集成 smoke**

```python
# backend/tests/test_smoke.py
import pytest
import requests

BASE = 'http://127.0.0.1:9091'

@pytest.fixture(scope='module')
def server_check():
    try:
        r = requests.get(BASE + '/api/meta/health', timeout=2)
        assert r.status_code == 200
    except Exception as e:
        pytest.skip(f'服务未启动: {e}')

@pytest.mark.parametrize('endpoint,payload', [
    ('/api/calc/gear/spur',       {'module': 3, 'teeth': 20}),
    ('/api/calc/gear/mesh',       {'module': 3, 'teeth1': 20, 'teeth2': 60}),
    ('/api/calc/spring/compression', {'wire_diameter': 4, 'mean_diameter': 30, 'coils': 10}),
    ('/api/calc/thread/metric',   {'nominal_diameter': 12, 'pitch': 1.75}),
    ('/api/calc/chain/sprocket',  {'pitch': 12.7, 'teeth': 17}),
    # ... 80+ 端点
])
def test_calc_endpoint(server_check, endpoint, payload):
    r = requests.post(BASE + endpoint, json=payload, timeout=5)
    assert r.status_code == 200, f'{endpoint} {r.text}'
    j = r.json()
    assert j['status'] == 'ok', f'{endpoint} {j}'
```

- [ ] **Step 2: 跑覆盖率**

```bash
python -m pytest backend/tests/ -v --cov=backend --cov-report=term-missing --cov-report=html
```
Target: 计算模块覆盖率 > 60%,API 蓝图 > 80%

- [ ] **Step 3: 跑 locust 压测 60 秒**

```bash
locust -f backend/tests/perf/locustfile.py --host=http://127.0.0.1:9091 --users=50 --spawn-rate=10 --run-time=60s --headless --html=perf-report.html
```
Target: p95 < 200ms, 0 个 5xx

- [ ] **Step 4: 提交**

```bash
git add backend/tests/
git commit -m "test: 全量 smoke + 覆盖率报告"
```

---

### Task 14: Phase 1 收尾 — 文档与打包

**Files:**
- Modify: `部署说明.md`
- Modify: `机械设计计算表.spec` (适配新结构)
- Create: `CHANGELOG.md`

- [ ] **Step 1: 更新部署说明,补充新 API**

在 `部署说明.md` 追加:
```markdown
## 新增 API (v2.1+)

| 路径 | 用途 |
|------|------|
| GET  /api/meta/health | 健康检查 |
| GET  /api/meta/categories | 13 大类分类树 |
| GET  /api/data/materials?q= | 材料搜索 |
| GET  /api/data/bearings | 深沟球轴承库 |
| GET  /api/data/constants | 物理常数 |
| POST /api/units/convert | 单位换算 |
| POST /api/calc/<module>/<func> | 统一计算端点 |

旧 URL `/api/calculate/*` 已自动重定向到 `/api/calc/*`。
```

- [ ] **Step 2: 更新 `机械设计计算表.spec`**

```python
# -*- mode: python ; coding: utf-8 -*-
# 适配新结构
added_files = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('data', 'data'),
]
# ...
```

- [ ] **Step 3: 创建 `CHANGELOG.md`**

```markdown
# Changelog

## v2.1.0 (2026-06-XX) — 架构重构

### 重构
- app.py 1390 行 → 200 行(应用工厂)
- 11 个 Blueprint 替代散落路由
- 前端 7 个 JS → Alpine.js 模块化
- 统一 API 响应格式 `{status, data, meta}`

### 新增
- 13 大类分类树(对齐《机械设计手册》)
- pytest 单元 + 集成 + locust 压测
- 统一错误处理
- API 缓存 (JSON 加载)

### 兼容
- 旧 URL `/api/calculate/*` → `/api/calc/*` 重定向

### 不变
- 所有计算公式(只迁移不修改)
- 数据 JSON (extracted_data.json)
- i18n zh/en/ja
```

- [ ] **Step 4: 提交**

```bash
git add 部署说明.md 机械设计计算表.spec CHANGELOG.md
git commit -m "docs: Phase 1 重构收尾"
```

---

## Phase 2: 功能扩展 (概要, 后续另写 plan)

> Phase 1 完成并验证后,单独创建 plan 文件执行。

### Task A: 公式查询 API (扫描 docstring, **不写新公式**)

**Files:**
- Create: `backend/utils/formula_index.py`
- Create: `backend/api/calculations/formulas.py`
- Create: `data/formulas.json` (由 build 脚本生成)
- Create: `backend/build_formulas.py`

- [ ] A1: 写 `build_formulas.py`,扫描 `backend/calculations/*.py` 的 docstring,提取
  - 函数名 → 中文/英文名
  - 参数列表
  - 公式 (LaTeX,如已存在)
  - 返回字段
- [ ] A2: 生成 `data/formulas.json`(由机器自动,**不手写**)
- [ ] A3: API `GET /api/formulas?module=&keyword=`
- [ ] A4: 前端"公式"Tab,全文搜索
- [ ] A5: 测试 + 提交

### Task B: 常数查询增强 (用现有 PHYSICAL_CONSTANTS)

**Files:**
- Modify: `backend/utils/units.py`
- Modify: `backend/api/units.py`

- [ ] B1: 扩展 `PHYSICAL_CONSTANTS` 分类(机械常用: g, R, NA, k, σ, h, c, ε0, μ0, R∞, me, mp, kB, atm, π)
- [ ] B2: API `GET /api/units/constants?category=mechanics|thermal|electromagnetic|universal`
- [ ] B3: 前端"常数"Tab
- [ ] B4: 测试 + 提交

### Task C: 计算历史 (SQLite)

**Files:**
- Create: `backend/utils/history_store.py`
- Create: `backend/api/calculations/history.py`

- [ ] C1: 写失败测试 `test_history_store.py`
- [ ] C2: 实现 `HistoryStore` (SQLite, 表 schema: id, ts, module, endpoint, inputs(JSON), outputs(JSON), duration_ms)
- [ ] C3: API `POST/GET/DELETE /api/history`
- [ ] C4: 接入装饰器 `@bp.post('/...')` 自动记录(用 before_request/after_request 钩子)
- [ ] C5: 前端"历史"侧边栏 + 重放
- [ ] C6: 测试 + 提交

### Task D: 分类树完整接入前端

- [ ] D1: `GET /api/meta/categories` 已在 Phase 1
- [ ] D2: 前端 13 个 Tab 按需激活
- [ ] D3: 测试 + 提交

### Task E: 部署优化

- [ ] E1: 重新打包 EXE (PyInstaller)
- [ ] E2: 性能 baseline 文档
- [ ] E3: 用户手册

---

## 三、风险与回退

| 风险 | 影响 | 回退策略 |
|------|------|----------|
| 蓝图迁移过程中路由丢失 | 高 | 旧 URL 重定向层(Task 9) 100% 兼容 |
| 性能不达预期 | 中 | 缓存粒度可调(JSON/索引) |
| 前端重写引入 bug | 中 | Phase 1 末保留旧 JS 备份;逐步切换 |
| locust 结果波动 | 低 | 跑 3 次取中位数 |

---

## 四、不在范围内 (Out of Scope)

- 新增计算公式 (用户要求"不编写公式与数据")
- 替换现有数据 JSON
- 数据库替换(SQLite 仅用于历史,业务数据保持 JSON)
- 多用户/权限系统
- CAD 集成 (P3 远期)
- AI 助手 (P3 远期)

---

## 五、验收标准 (Phase 1 结束)

- [ ] `backend/app.py` < 200 行
- [ ] 11+ Blueprint 全部注册
- [ ] 旧 URL 100% 兼容(跑通 test_all.py)
- [ ] pytest 单元 + 集成 100% 通过
- [ ] 计算模块覆盖率 > 60%,API 蓝图 > 80%
- [ ] locust 50 用户 60s: p95 < 200ms, 0 个 5xx
- [ ] 前端 13 大类 Tab 至少 3 个可用(齿轮/弹簧/单位换算)
- [ ] 不修改任何 `calculations/*.py` 计算逻辑
- [ ] 不修改 `data/extracted_data.json`

---

**完成 Phase 1 后,创建独立 plan 文件执行 Phase 2 (公式查询/常数/历史/分类树)。**
