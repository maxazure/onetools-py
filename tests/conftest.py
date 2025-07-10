"""Test configuration and fixtures"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import create_app
from app.core.config import Settings, update_settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test settings fixture"""
    # Override settings for testing
    test_config = {
        "environment": "testing",
        "debug": True,
        "database": {
            "sqlite_path": "test_data/test_onetools.db"
        },
        "logging": {
            "level": "DEBUG",
            "format": "console"
        }
    }
    
    return update_settings(**test_config)


@pytest.fixture(scope="session")
def app(test_settings):
    """Create test FastAPI app"""
    return create_app()


@pytest.fixture(scope="session")
def client(app) -> TestClient:
    """Create test client"""
    return TestClient(app)


@pytest.fixture(scope="session")
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com", 
        "status": "active"
    }


@pytest.fixture
def sample_query_request():
    """Sample query request for testing"""
    return {
        "username": "test",
        "status": "active",
        "page": 1,
        "size": 20
    }