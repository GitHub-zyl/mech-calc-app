"""集中错误处理 - 避免 try/except 散落"""
from .responses import error


def register_error_handlers(app):
    """注册全局错误处理器"""

    @app.errorhandler(400)
    def bad_request(e):
        return error('请求格式错误: ' + str(e), code=400)

    @app.errorhandler(404)
    def not_found(e):
        return error('资源不存在: ' + str(e), code=404)

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error('方法不允许: ' + str(e), code=405)

    @app.errorhandler(422)
    def unprocessable(e):
        return error('参数无法处理: ' + str(e), code=422)

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception('Internal error: %s', e)
        return error('服务器内部错误', code=500)
