"""
机械设计常用计算表 - Flask App Factory

v2.1.0 起改为应用工厂模式:
- create_app(testing=False) 返回配置好的 Flask 实例
- 支持测试时传入 testing=True 启用测试模式
- 蓝图按需注册, 旧 URL 重定向在 compat 层
- 直接 python app.py 仍可启动 (向后兼容)
"""
import sys
from pathlib import Path

# 确保能找到 calculations 模块 (与原 app.py 一致)
# 同时把项目根目录加入 path, 以便 `from backend.xxx import` 工作
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask

from backend.config import Config, TestConfig
from backend.api.errors import register_error_handlers
from backend.api.meta import bp as meta_bp


def create_app(testing=False):
    """应用工厂

    Args:
        testing: True 时使用 TestConfig, 关闭外部依赖

    Returns:
        Flask app
    """
    cfg = TestConfig if testing else Config
    app = Flask(__name__,
                template_folder=str(cfg.BASE_DIR / 'templates'),
                static_folder=str(cfg.BASE_DIR / 'static'))
    app.config.from_object(cfg)

    # 全局错误处理
    register_error_handlers(app)

    # 预热 JSON 缓存 (业务数据, 非启动阻塞)
    try:
        from backend.utils.db import load_json
        load_json(cfg.DATA_FILE)
        load_json(cfg.I18N_FILE)
    except FileNotFoundError:
        # 测试或首次启动时数据可能不存在, 跳过
        pass

    # 蓝图注册
    app.register_blueprint(meta_bp)
    # 后续 Task 会追加: data_bp, units_bp, calculations.*

    # 根路径
    @app.route('/')
    def index():
        from flask import current_app
        idx = Path(current_app.template_folder) / 'index.html'
        if idx.exists():
            with open(idx, 'r', encoding='utf-8') as f:
                return current_app.response_class(f.read(), mimetype='text/html')
        return '<h1>Template not found</h1>', 404

    # data 静态文件 (与原 app.py 一致)
    @app.route('/data/<path:filename>')
    def serve_data(filename):
        from backend.api.responses import error
        from flask import jsonify
        data_dir = Path(__file__).parent.parent / 'data'
        filepath = data_dir / filename
        if filepath.exists() and filename.endswith('.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                return app.response_class(f.read(), mimetype='application/json')
        return error('File not found', code=404)

    return app


# 保留直接 python app.py 启动的兼容性
if __name__ == '__main__':
    app = create_app()
    cfg = Config
    print('=' * 50)
    print(f'Mech Design Calculator v{cfg.__dict__.get("APP_VERSION", "2.1.0")}')
    print(f'Start: http://{cfg.HOST}:{cfg.PORT}')
    print('Press Ctrl+C to stop')
    print('=' * 50)
    app.run(host=cfg.HOST, port=cfg.PORT, debug=cfg.DEBUG)
