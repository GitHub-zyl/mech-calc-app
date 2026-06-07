"""单元测试: backend/api/compat.py (覆盖率 93% → 100%)

覆盖目标:
- legacy_calculate: GET 和 POST 都应重定向 (L61, 67)
- legacy_material_search / info: 308 重定向
- legacy_fit_recommendations / motor_knowledge: 200 + 占位
"""
import json
import pytest

from backend.app import create_app


class TestLegacyCompat:
    """旧 API 路径兼容 (覆盖 L61, 67)."""

    @pytest.fixture
    def client(self):
        app = create_app(testing=True)
        return app.test_client()

    def test_legacy_calculate_get_308(self, client):
        """GET /api/calculate/... → 308 重定向."""
        r = client.get('/api/calculate/gear/spur')
        assert r.status_code == 308
        # 重定向 Location 应指向新 API
        assert '/api/calc/gear/spur' in r.headers.get('Location', '')

    def test_legacy_calculate_post_308(self, client):
        """POST /api/calculate/... → 308 重定向."""
        r = client.post('/api/calculate/bearing/life',
                        json={'C': 10, 'P': 5, 'n': 1000})
        assert r.status_code == 308
        assert '/api/calc/bearing/life' in r.headers.get('Location', '')

    def test_legacy_calculate_nested_path(self, client):
        """多级路径: /api/calculate/X/Y/Z."""
        r = client.get('/api/calculate/gear/helical/calc')
        assert r.status_code == 308
        assert '/api/calc/gear/helical/calc' in r.headers.get('Location', '')

    def test_legacy_material_search_redirect(self, client):
        """/api/material/search → /api/data/materials."""
        r = client.get('/api/material/search?q=steel')
        assert r.status_code == 308
        location = r.headers.get('Location', '')
        assert '/api/data/materials' in location
        assert 'q=steel' in location

    def test_legacy_material_search_empty_query(self, client):
        """空查询字符串."""
        r = client.get('/api/material/search?q=')
        assert r.status_code == 308
        assert 'q=' in r.headers.get('Location', '')

    def test_legacy_material_info_redirect(self, client):
        """/api/material/info?name=45 → /api/data/materials/45."""
        r = client.get('/api/material/info?name=45%E9%92%A2')
        assert r.status_code == 308
        location = r.headers.get('Location', '')
        assert '/api/data/materials' in location

    def test_legacy_fit_recommendations_placeholder(self, client):
        """/api/data/fit_recommendations: 返回实际数据 + 数据结构校验."""
        r = client.get('/api/data/fit_recommendations')
        assert r.status_code == 200
        body = json.loads(r.data)
        assert body['status'] == 'ok'
        # 实际返回非空数据 (Phase 2 已注入), 验证数据结构
        assert 'data' in body
        assert isinstance(body['data'], dict)
        assert 'items' in body['data']
        assert isinstance(body['data']['items'], list)

    def test_legacy_motor_knowledge_placeholder(self, client):
        """/api/data/motor_knowledge: 返回实际数据 + 数据结构校验."""
        r = client.get('/api/data/motor_knowledge')
        assert r.status_code == 200
        body = json.loads(r.data)
        assert body['status'] == 'ok'
        # 实际返回非空数据 (Phase 2 已注入), 验证数据结构
        assert 'data' in body
        assert isinstance(body['data'], dict)
        assert 'items' in body['data']
        assert isinstance(body['data']['items'], list)
