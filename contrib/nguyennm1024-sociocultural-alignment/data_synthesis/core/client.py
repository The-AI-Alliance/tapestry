"""Model client wrapper. Defaults to Moonshot's Kimi K2.6 over the
OpenAI-compatible endpoint, but the base_url/api_key are overridable so the
same library can drive other backends."""
import os

import httpx
import openai
from dotenv import load_dotenv

# override=True so the project's `.env` wins over any stale exports in
# the user's shell (.zshrc / .bash_profile). Avoids the surprise of an
# old DEEPSEEK_API_KEY in zshrc shadowing a fresh one in .env.
load_dotenv(override=True)

DEFAULT_MODEL = "kimi-k2.6"
DEFAULT_BASE_URL = "https://api.moonshot.ai/v1"
DEFAULT_API_KEY = os.environ.get("KIMI_API_KEY")

# DeepSeek V4 Pro — fast reasoning model, OpenAI-compatible. Returns
# `reasoning_content` separately like Kimi K2.6. Used as a fallback when
# the Kimi account balance is exhausted.
DEEPSEEK_MODEL = "deepseek-v4-pro"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# Non-streaming question-gen calls to Kimi K2.6 routinely take 130-200s when
# Moonshot is loaded (reasoning trace + 20 questions output). For non-streaming,
# `read` is the total time to receive the response — too tight a value kills
# slow-but-progressing calls. 300s gives ~2x headroom over typical and still
# fails fast on truly hung connections.
# Long-term fix: switch question gen to streaming so `read` is per-chunk and
# 120s suffices for catching zombies.
DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=15.0)


def make_client(
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: httpx.Timeout | None = None,
) -> openai.Client:
    key = api_key or DEFAULT_API_KEY
    if not key:
        raise RuntimeError(
            "KIMI_API_KEY not set. Create a .env file or export the variable, "
            "or pass api_key= explicitly."
        )
    return openai.Client(
        api_key=key,
        base_url=base_url or DEFAULT_BASE_URL,
        timeout=timeout or DEFAULT_TIMEOUT,
    )


def make_deepseek_client(
    api_key: str | None = None,
    timeout: httpx.Timeout | None = None,
) -> openai.Client:
    """DeepSeek V4 Pro client. Used as fallback when Kimi is exhausted."""
    key = api_key or DEEPSEEK_API_KEY
    if not key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY not set. Add it to .env or pass api_key= explicitly."
        )
    return openai.Client(
        api_key=key,
        base_url=DEEPSEEK_BASE_URL,
        timeout=timeout or DEFAULT_TIMEOUT,
    )
