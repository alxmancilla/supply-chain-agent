from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "supply_chain_agent"

    realm_id: str = "demo_realm"
    agent_id: str = "supply_chain_resolution_agent"
    user_id: str = "planner_001"

    grove_api_key: SecretStr | None = None
    grove_base_url: str = (
        "https://grove-gateway-prod.azure-api.net/"
        "grove-foundry-prod/openai/v1"
    )
    grove_model: str = "gpt-5.5"

    atlas_embedding_model: str = "voyage-4"
    atlas_rerank_model: str = "rerank-2.5-lite"
    atlas_native_rerank_enabled: bool = True

    knowledge_vector_index: str = "knowledge_corpus_autoembed"
    memory_vector_index: str = "agent_memories_autoembed"
    episode_vector_index: str = "agent_episodes_autoembed"
    knowledge_search_index: str = "knowledge_corpus_search"


@lru_cache
def get_settings() -> Settings:
    return Settings()