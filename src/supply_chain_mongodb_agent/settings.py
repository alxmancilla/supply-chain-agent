from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    demo_mode: Literal["local", "atlas"] = "local"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "supply_chain_agent"
    mongodb_server_selection_timeout_ms: int = 5000

    realm_id: str = "demo_realm"
    agent_id: str = "supply_chain_resolution_agent"
    user_id: str = "planner_001"

    llm_provider: str = "openai_compatible"
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    llm_model: str = "gpt-4.1-mini"
    llm_api_key_header: str | None = None
    llm_use_responses_api: bool | None = None

    # Legacy Grove settings are supported so existing internal .env files keep working.
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

    @property
    def llm_api_key_configured(self) -> bool:
        return self._secret_configured(self.llm_api_key) or self.grove_api_key_configured

    @property
    def grove_api_key_configured(self) -> bool:
        return self._secret_configured(self.grove_api_key)

    @property
    def effective_llm_provider(self) -> str:
        if self._uses_legacy_grove_settings:
            return "grove"
        return self.llm_provider

    @property
    def effective_llm_api_key(self) -> SecretStr | None:
        if self._secret_configured(self.llm_api_key):
            return self.llm_api_key
        if self.grove_api_key_configured:
            return self.grove_api_key
        return None

    @property
    def effective_llm_base_url(self) -> str | None:
        if self.llm_base_url:
            return self.llm_base_url.rstrip("/")
        if self.effective_llm_provider == "grove":
            return self.grove_base_url.rstrip("/")
        return None

    @property
    def effective_llm_model(self) -> str:
        if self._uses_legacy_grove_settings:
            return self.grove_model
        return self.llm_model

    @property
    def effective_llm_api_key_header(self) -> str | None:
        if self.llm_api_key_header:
            return self.llm_api_key_header
        if self.effective_llm_provider == "grove":
            return "api-key"
        return None

    @property
    def effective_llm_use_responses_api(self) -> bool:
        if self.llm_use_responses_api is not None:
            return self.llm_use_responses_api
        return self.effective_llm_provider == "grove"

    @property
    def _uses_legacy_grove_settings(self) -> bool:
        return not self._secret_configured(self.llm_api_key) and self.grove_api_key_configured

    @staticmethod
    def _secret_configured(secret: SecretStr | None) -> bool:
        if secret is None:
            return False
        value = secret.get_secret_value().strip()
        return bool(value and not value.startswith("<"))


@lru_cache
def get_settings() -> Settings:
    return Settings()