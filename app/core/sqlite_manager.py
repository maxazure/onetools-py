"""SQLite配置数据库管理器 - 仅用于存储应用配置"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import DatabaseConfig, settings
from app.core.logging import LoggerMixin, get_logger

logger = get_logger(__name__)


class SQLiteConfigManager(LoggerMixin):
    """SQLite配置数据库管理器 - 专门用于存储应用配置数据"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__()
        self.config = config
        self._engine: Optional[AsyncEngine] = None
        self._session_maker: Optional[async_sessionmaker] = None
        self._metadata = MetaData()
        
        # 初始化SQLite引擎
        self._setup_engine()
    
    def _setup_engine(self) -> None:
        """设置SQLite引擎"""
        try:
            # 确保数据目录存在
            db_path = Path(self.config.sqlite_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            self._engine = create_async_engine(
                self.config.sqlite_connection_string,
                poolclass=NullPool,  # SQLite不需要连接池
                echo=settings.debug,
                future=True,
            )
            
            self._session_maker = async_sessionmaker(
                self._engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            logger.info("SQLite config engine created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create SQLite config engine: {e}")
            raise RuntimeError(f"SQLite config engine creation failed: {e}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取配置数据库会话"""
        if not self._session_maker:
            raise ValueError("SQLite session maker not available")
        
        async with self._session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[AsyncConnection, None]:
        """获取配置数据库连接"""
        if not self._engine:
            raise ValueError("SQLite engine not available")
        
        async with self._engine.begin() as conn:
            yield conn
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """执行配置数据库事务"""
        async with self.get_session() as session:
            async with session.begin():
                try:
                    yield session
                except Exception as e:
                    self.log_error("SQLite config transaction failed, rolling back", error=e)
                    raise
    
    async def execute_query(self, query: str, parameters: Optional[tuple] = None) -> Any:
        """执行SQLite查询并返回结果"""
        if not self._engine:
            raise ValueError("SQLite engine not available")
        
        async with self._engine.begin() as conn:
            # 将tuple参数转换为字典格式
            if parameters:
                # 对于DELETE FROM table WHERE id = ? 这种情况，SQLAlchemy需要字典格式
                param_dict = {}
                for i, param in enumerate(parameters):
                    param_dict[f'param_{i}'] = param
                # 修改查询语句以使用命名参数
                query = query.replace('?', f':param_{0}')
                result = await conn.execute(text(query), param_dict)
            else:
                result = await conn.execute(text(query))
            return result

    async def close(self) -> None:
        """关闭SQLite连接"""
        if self._engine:
            await self._engine.dispose()
            self.log_info("SQLite config engine closed")