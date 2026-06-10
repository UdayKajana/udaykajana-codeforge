"""
Provider-agnostic LLM configuration for DSPy agents.

Detects key type from the key prefix:
  - OpenRouter : starts with  'sk-or-v1-'
  - Azure      : everything else (base-64 encoded resource key)

Call get_lm(api_key) once per request/session; it calls dspy.configure()
so all downstream agents pick it up automatically.
"""

import os
import ssl
import litellm
import dspy

# Disable SSL verification for corporate proxy environments where the proxy
# intercepts HTTPS with its own certificate that Python's default trust store
# does not recognise (common on Windows enterprise networks).
os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["CURL_CA_BUNDLE"]    = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
litellm.ssl_verify = False
ssl._create_default_https_context = ssl._create_unverified_context

# ── Azure defaults (override via env or pass explicitly) ──────────────────────
AZURE_ENDPOINT    = "https://synapt-softbank.openai.azure.com"
AZURE_API_VERSION = "2025-01-01-preview"
AZURE_DEPLOYMENT  = "gpt-4o"

# ── OpenRouter defaults ───────────────────────────────────────────────────────
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL    = "openai/gpt-4o"


def detect_provider(api_key: str) -> str:
    """Return 'openrouter' or 'azure' based on key format."""
    return "openrouter" if api_key.strip().startswith("sk-or-v1-") else "azure"


def get_lm(
    api_key: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> dspy.LM:
    """
    Build and return a DSPy LM object without touching global settings.
    Use dspy.context(lm=...) in threads, or dspy.configure(lm=...) from the main thread.

    Azure      → azure/gpt-4o  via  AZURE_ENDPOINT
    OpenRouter → openai/gpt-4o via  openrouter.ai/api/v1
    """
    provider = detect_provider(api_key)

    if provider == "openrouter":
        return dspy.LM(
            model=OPENROUTER_MODEL,
            api_key=api_key.strip(),
            api_base=OPENROUTER_BASE_URL,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:  # azure
        return dspy.LM(
            model=f"azure/{AZURE_DEPLOYMENT}",
            api_key=api_key.strip(),
            api_base=AZURE_ENDPOINT,
            api_version=AZURE_API_VERSION,
            temperature=temperature,
            max_tokens=max_tokens,
        )
