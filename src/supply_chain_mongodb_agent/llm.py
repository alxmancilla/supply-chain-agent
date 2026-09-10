from langchain_openai import ChatOpenAI

from supply_chain_mongodb_agent.settings import Settings, get_settings


def build_chat_model(settings: Settings | None = None) -> ChatOpenAI:
    """Build the connected-mode chat model from provider-neutral LLM settings."""
    settings = settings or get_settings()
    llm_key = settings.effective_llm_api_key
    if llm_key is None:
        raise ValueError("LLM_API_KEY is required when DEMO_MODE=atlas")

    api_key = llm_key.get_secret_value()
    kwargs = {
        "model": settings.effective_llm_model,
        "base_url": settings.effective_llm_base_url,
        "use_responses_api": settings.effective_llm_use_responses_api,
        "temperature": 0,
    }
    if settings.effective_llm_api_key_header:
        kwargs["api_key"] = "header-auth"
        kwargs["default_headers"] = {settings.effective_llm_api_key_header: api_key}
    else:
        kwargs["api_key"] = api_key
    return ChatOpenAI(**{key: value for key, value in kwargs.items() if value is not None})