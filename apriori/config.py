from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Database
    database_url: str = "postgresql+asyncpg://apriori:apriori@localhost:5432/apriori"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # vLLM
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_model_name: str = "meta-llama/Meta-Llama-3.1-70B-Instruct"

    # Anthropic
    anthropic_api_key: str = ""
    # Model to use: "claude-haiku-4-5-20251001" (fast, cheap) or "claude-sonnet-4-6" (quality)
    llm_model: str = "claude-haiku-4-5-20251001"
    # LLM provider: "anthropic" or "openai" (for vLLM / OpenAI-compatible endpoints)
    llm_provider: str = "anthropic"

    # Temporal
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "apriori"
    temporal_task_queue: str = "apriori-simulations"

    # LangSmith
    langchain_tracing_v2: bool = True
    langchain_api_key: str = ""
    langchain_project: str = "apriori"
    langsmith_api_key: str = ""
    langsmith_project: str = "apriori-rfm"
    langsmith_tracing: bool = True

    # Mem0
    mem0_api_key: str = ""

    # Clerk
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    clerk_issuer: str = ""
    clerk_webhook_secret: str = ""
    resend_api_key: str = ""

    # Frontend
    frontend_url: str = "http://localhost:3000"
    cors_allowed_origins: str = "http://localhost:3000"

    # Simulation
    default_num_simulations: int = 100
    max_timeline_turns: int = 50
    belief_collapse_kl_threshold: float = 2.0


settings = Settings()
