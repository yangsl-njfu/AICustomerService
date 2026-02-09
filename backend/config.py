"""
应用配置模块
"""
import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "AI客服系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "ai_customer_service"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    # FAISS配置
    FAISS_PERSIST_DIRECTORY: str = "./data/faiss"
    
    # JWT配置
    JWT_SECRET_KEY: str = "your-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # LLM 配置（支持 OpenAI 和 DeepSeek）
    LLM_PROVIDER: str = "deepseek"  # 可选: openai, deepseek
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEEPSEEK_API_KEY: str = "sk-97b7c12d6b2f4b10b96798ac85f4dbf4"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    
    # 硅基流动配置（用于 Embeddings）
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_EMBEDDING_MODEL: str = "BAAI/bge-m3"
    
    # 文件上传配置
    UPLOAD_DIR: str = "./data/uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "pdf,doc,docx,txt,png,jpg,jpeg"
    
    # 系统配置
    MAX_CONCURRENT_SESSIONS: int = 50
    CONTEXT_MAX_HISTORY: int = 20
    RETRIEVAL_TOP_K: int = 3
    REQUEST_TIMEOUT: int = 30
    
    # 高级RAG配置
    RAG_USE_HYBRID_SEARCH: bool = True  # 是否使用混合检索(向量+BM25)
    RAG_USE_RERANK: bool = True  # 是否使用LLM重排序
    RAG_USE_QUERY_REWRITE: bool = True  # 是否使用查询改写
    RAG_RERANK_TOP_K: int = 10  # 重排序前保留的候选文档数
    RAG_SIMILARITY_THRESHOLD: float = 0.7  # 相似度阈值
    
    # CORS配置
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def database_url(self) -> str:
        """获取数据库连接URL"""
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
    
    @property
    def LLM_MODEL(self) -> str:
        """根据provider返回对应的模型"""
        if self.LLM_PROVIDER == "deepseek":
            return self.DEEPSEEK_MODEL
        return self.OPENAI_MODEL
    
    @property
    def LLM_API_KEY(self) -> str:
        """根据provider返回对应的API Key"""
        if self.LLM_PROVIDER == "deepseek":
            return self.DEEPSEEK_API_KEY
        return self.OPENAI_API_KEY
    
    @property
    def LLM_BASE_URL(self) -> str:
        """根据provider返回对应的Base URL"""
        if self.LLM_PROVIDER == "deepseek":
            return self.DEEPSEEK_BASE_URL
        return self.OPENAI_BASE_URL
    
    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """获取CORS允许的源列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """获取允许的文件扩展名列表"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    class Config:
        # 尝试多个可能的 .env 文件位置
        env_file = ".env" if os.path.exists(".env") else "backend/.env"
        case_sensitive = True


# 全局配置实例
settings = Settings()
