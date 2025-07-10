"""Configuration management with Pydantic Settings"""

from typing import List, Optional
from functools import lru_cache

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    """Database configuration"""
    
    # SQL Server configuration
    # 注意：仅支持Windows集成认证
    # 数据库名称通过SQL语句指定，不在连接字符串中硬编码
    sqlserver_host: str = Field(default="localhost\\SQLEXPRESS", env="SQLSERVER_HOST")
    sqlserver_port: int = Field(default=1433, env="SQLSERVER_PORT")
    
    # SQLite configuration (config database)
    sqlite_path: str = Field(default="data/onetools.db", env="SQLITE_PATH")
    
    # Connection pool settings
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    @property
    def sqlserver_connection_string(self) -> str:
        """Generate SQL Server ODBC connection string
        
        注意：仅支持Windows集成认证，不支持SQL Server认证
        数据库名称通过SQL语句指定，不在连接字符串中硬编码
        """
        # 使用正确的SQLAlchemy + pyodbc格式
        driver = "ODBC+Driver+17+for+SQL+Server"
        
        # 强制使用Windows Authentication，不指定数据库
        return (
            f"mssql+pyodbc://@{self.sqlserver_host}/"
            f"?driver={driver}"
            f"&Trusted_Connection=yes&TrustServerCertificate=yes&Encrypt=no"
        )
    
    @property
    def sqlite_connection_string(self) -> str:
        """Generate SQLite connection string"""
        return f"sqlite+aiosqlite:///{self.sqlite_path}"


class ServerConfig(BaseModel):
    """Server configuration"""
    
    host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    port: int = Field(default=15008, env="SERVER_PORT")
    reload: bool = Field(default=False, env="SERVER_RELOAD")
    workers: int = Field(default=1, env="SERVER_WORKERS")
    
    # CORS settings
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_methods: List[str] = Field(default=["*"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")


class LoggingConfig(BaseModel):
    """Logging configuration"""
    
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")  # json or console
    file_path: Optional[str] = Field(default="logs/onetools.log", env="LOG_FILE_PATH")
    max_file_size: str = Field(default="10MB", env="LOG_MAX_FILE_SIZE")
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    @field_validator("level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class ModuleConfig(BaseModel):
    """Module configuration"""
    
    enabled_modules: List[str] = Field(
        default=["transaction_query", "custom_query", "dynamic_query"],
        env="ENABLED_MODULES"
    )
    auto_discovery: bool = Field(default=True, env="MODULE_AUTO_DISCOVERY")
    cache_enabled: bool = Field(default=True, env="MODULE_CACHE_ENABLED")
    cache_ttl: int = Field(default=300, env="MODULE_CACHE_TTL")  # seconds



class Settings(BaseSettings):
    """Main application settings"""
    
    # Application metadata
    app_name: str = Field(default="OneTools", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Logging configuration directly
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="console", env="LOG_FORMAT")
    log_file_path: Optional[str] = Field(default="logs/onetools.log", env="LOG_FILE_PATH")
    log_max_file_size: str = Field(default="10MB", env="LOG_MAX_FILE_SIZE")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Database configuration directly
    # 注意：仅支持Windows集成认证
    # 数据库名称通过SQL语句指定，不在连接字符串中硬编码
    sqlserver_host: str = Field(default="localhost\\SQLEXPRESS", env="SQLSERVER_HOST")
    sqlserver_port: int = Field(default=1433, env="SQLSERVER_PORT")
    
    # Server configuration directly
    server_host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(default=15008, env="SERVER_PORT")
    
    # Additional settings
    hot_reload_enabled: bool = Field(default=True, env="HOT_RELOAD_ENABLED")
    
    @property
    def database(self) -> DatabaseConfig:
        """Get database configuration"""
        return DatabaseConfig(
            sqlserver_host=self.sqlserver_host,
            sqlserver_port=self.sqlserver_port
        )
    
    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration"""
        return LoggingConfig(
            level=self.log_level,
            format=self.log_format,
            file_path=self.log_file_path,
            max_file_size=self.log_max_file_size,
            backup_count=self.log_backup_count
        )
    
    @property
    def server(self) -> ServerConfig:
        """Get server configuration"""
        return ServerConfig(
            host=self.server_host,
            port=self.server_port
        )
    
    @property
    def modules(self) -> ModuleConfig:
        """Get modules configuration"""
        return ModuleConfig()
    
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
        
    @field_validator("environment")
    def validate_environment(cls, v):
        """Validate environment"""
        valid_envs = ["development", "testing", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()
    
    


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    return settings


# Global settings instance
settings = get_settings()


def reload_settings() -> Settings:
    """Reload settings (clear cache and reload)"""
    get_settings.cache_clear()
    return get_settings()


def update_settings(**kwargs) -> Settings:
    """Update settings dynamically"""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    return settings