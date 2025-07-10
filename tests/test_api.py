"""API端点测试"""

import pytest
from fastapi.testclient import TestClient


class TestAPIEndpoints:
    """API端点测试类"""
    
    def test_root_endpoint(self, client: TestClient):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "OneTools" in data["data"]["name"]
    
    def test_health_endpoint(self, client: TestClient):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "status" in data["data"]
    
    def test_api_docs_endpoint(self, client: TestClient):
        """测试API文档端点"""
        response = client.get("/api/docs")
        assert response.status_code == 200
    
    def test_openapi_endpoint(self, client: TestClient):
        """测试OpenAPI端点"""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestUserAPI:
    """用户API测试"""
    
    def test_get_user_parameters(self, client: TestClient):
        """测试获取用户查询参数"""
        response = client.get("/api/v1/users/parameters")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    @pytest.mark.skip(reason="需要数据库连接")
    def test_query_users(self, client: TestClient, sample_query_request):
        """测试用户查询"""
        response = client.post("/api/v1/users/query", json=sample_query_request)
        
        # 如果数据库连接失败，应该返回503
        if response.status_code == 503:
            pytest.skip("数据库连接不可用")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestCustomQueryAPI:
    """自定义查询API测试"""
    
    def test_get_custom_query_parameters(self, client: TestClient):
        """测试获取自定义查询参数"""
        response = client.get("/api/v1/custom/parameters")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_validate_sql(self, client: TestClient):
        """测试SQL验证"""
        test_sql = {"sql": "SELECT 1"}
        response = client.post("/api/v1/custom/validate", json=test_sql)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "valid" in data["data"]
    
    def test_validate_dangerous_sql(self, client: TestClient):
        """测试危险SQL验证"""
        dangerous_sql = {"sql": "DROP TABLE users"}
        response = client.post("/api/v1/custom/validate", json=dangerous_sql)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["valid"] is False
        assert data["data"]["is_safe"] is False


class TestDatabaseAPI:
    """数据库API测试"""
    
    def test_database_health_check(self, client: TestClient):
        """测试数据库健康检查"""
        response = client.get("/api/v1/database/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "database_status" in data["data"]
    
    def test_get_connection_status(self, client: TestClient):
        """测试获取连接状态"""
        response = client.get("/api/v1/database/connection-status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_test_connection(self, client: TestClient):
        """测试数据库连接测试"""
        response = client.post("/api/v1/database/test-connection?database_name=sqlite")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "database_name" in data["data"]