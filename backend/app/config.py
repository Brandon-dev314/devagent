from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):


    model_config = SettingsConfigDict(
        env_file=".env",

        env_file_encoding="utf-8",

        extra="ignore",
    )

    app_name: str = "DevAgent"
    app_version: str = "0.1.0"
    debug: bool = Field(
        default=True,
        description="En True activa reload, logs verbose, docs de Swagger. "
        "NUNCA True en producción.",
    )
    
    api_prefix: str = "/api/v1"
    allowed_origins: str = Field(
        default="http://localhost:3000",
        description="Dominios permitidos para CORS, separados por coma. "
        "En producción: https://tu-frontend.vercel.app",
    )

    openai_api_key: str = Field(
        default="",
        description="API key de OpenAI. Vacío = el agente no puede generar respuestas.",
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="Modelo a usar. gpt-4o-mini es barato para desarrollo. "
        "En producción podrías cambiar a gpt-4o o claude-sonnet.",
    )
    llm_temperature: float = Field(
        default=0.1,
        description="Qué tan 'creativo' es el LLM. 0.1 = muy determinista "
        "(bueno para soporte técnico donde quieres respuestas consistentes).",
    )
    llm_max_tokens: int = Field(
        default=2048,
        description="Máximo de tokens en la respuesta del LLM.",
    )

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "devagent_docs"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "devagent"
    postgres_password: str = "devagent_dev"
    postgres_db: str = "devagent"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    chunk_size: int = Field(
        default=512,
        description="Tamaño de cada chunk en tokens. "
        "512 es un buen balance: suficiente contexto sin diluir la relevancia.",
    )
    chunk_overlap: int = Field(
        default=50,
        description="Tokens de overlap entre chunks consecutivos. "
        "Evita que una idea que cae en la frontera de dos chunks se pierda.",
    )
    top_k: int = Field(
        default=5,
        description="Cuántos chunks recuperar del vector store. "
        "Más = más contexto pero más tokens (más caro y más lento).",
    )

    github_token: str = Field(
        default="",
        description="Personal access token de GitHub para crear issues, leer repos, etc.",
    )

settings = Settings()