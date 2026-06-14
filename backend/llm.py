"""Single LLM instance shared across all chains and agents."""

from langchain_openai import ChatOpenAI

from backend import config


def _build_llm() -> ChatOpenAI:
    """Return a configured ChatOpenAI. Prefers OpenAI if a key is set, else falls back to Groq."""
    if config.OPENAI_API_KEY:
        return ChatOpenAI(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
            api_key=config.OPENAI_API_KEY,
        )

    if not config.GROQ_API_KEY:
        raise RuntimeError(
            "No LLM credentials found. Set either OPENAI_API_KEY or GROQ_API_KEY in your environment."
        )

    return ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=config.LLM_TEMPERATURE,
        api_key=config.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )


llm = _build_llm()
