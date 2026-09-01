from langchain_openai import ChatOpenAI

from supply_chain_mongodb_agent.settings import Settings, get_settings


def build_grove_chat(settings: Settings | None = None) -> ChatOpenAI:
    settings = settings or get_settings()
    if settings.grove_api_key is None:
        raise ValueError("GROVE_API_KEY is required to build the Grove chat model")
    grove_key = settings.grove_api_key.get_secret_value()
    return ChatOpenAI(
        model=settings.grove_model,
        base_url=settings.grove_base_url.rstrip("/"),
        api_key="grove-header-auth",
        default_headers={"api-key": grove_key},
        use_responses_api=True,
        temperature=0,
    )