import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


load_dotenv()


# Groq exposes an OpenAI-compatible endpoint (free tier available).
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"


def get_model_name():
    return os.getenv("CODEPILOT_MODEL", DEFAULT_MODEL)


def get_token():
    return os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")


def api_key_configured():
    return bool(get_token())


def get_llm():

    if not api_key_configured():
        raise RuntimeError(
            "GROQ_API_KEY is not set. Create a free key at "
            "https://console.groq.com/keys and add it to .env."
        )

    return ChatOpenAI(
        model=get_model_name(),
        temperature=float(
            os.getenv("CODEPILOT_TEMPERATURE", "0.2")
        ),
        max_tokens=2048,
        api_key=get_token(),
        base_url=GROQ_BASE_URL
    )
