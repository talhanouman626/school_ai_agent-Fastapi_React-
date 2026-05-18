# ============================================================
# llm_manager.py — API key loading + model rotation (FastAPI version)
# st.session_state hata diya — state ab main.py mein manage hogi
# ============================================================
import os
import logging
from langchain_groq import ChatGroq
from config import MODEL_POOL, ROTATION_THRESHOLD

logger = logging.getLogger(__name__)


def load_api_keys() -> list[str]:
    keys = []
    i = 1
    while True:
        k = os.getenv(f"GROQ_API_KEY_{i}")
        if not k:
            break
        keys.append(k.strip())
        i += 1
    if not keys:
        single = os.getenv("GROQ_API_KEY", "").strip()
        if single:
            keys.append(single)
    return keys


def get_usage_key(key_idx: int, model_idx: int) -> str:
    return f"{key_idx}:{model_idx}"


def record_token_usage(
    token_usage: dict, key_idx: int, model_idx: int, tokens_used: int
) -> dict:
    k = get_usage_key(key_idx, model_idx)
    token_usage[k] = token_usage.get(k, 0) + tokens_used
    return token_usage


def get_usage_percent(token_usage: dict, key_idx: int, model_idx: int) -> float:
    k     = get_usage_key(key_idx, model_idx)
    used  = token_usage.get(k, 0)
    limit = MODEL_POOL[model_idx]["tpd_limit"]
    return used / limit


def get_active_llm(
    keys: list[str],
    token_usage: dict,
    active_key_idx: int,
    active_model_idx: int,
) -> tuple[ChatGroq | None, int, int]:
    """
    Returns (llm, active_key_idx, active_model_idx)
    Indexes update hote hain agar rotation hoi
    """
    total_keys   = len(keys)
    total_models = len(MODEL_POOL)
    ki, mi       = active_key_idx, active_model_idx

    for _ in range(total_keys * total_models):
        if get_usage_percent(token_usage, ki, mi) < ROTATION_THRESHOLD:
            llm = ChatGroq(
                temperature=0.1,
                model_name=MODEL_POOL[mi]["model_id"],
                groq_api_key=keys[ki],
            )
            return llm, ki, mi

        logger.error(f"Key {ki} + Model {MODEL_POOL[mi]['label']} at 90% — rotating.")
        mi += 1
        if mi >= total_models:
            mi = 0
            ki = (ki + 1) % total_keys

    return None, ki, mi


def handle_rate_limit_error(
    token_usage: dict, key_idx: int, model_idx: int
) -> dict:
    k = get_usage_key(key_idx, model_idx)
    token_usage[k] = MODEL_POOL[model_idx]["tpd_limit"]
    logger.error(f"429 received — forced rotation from key {key_idx}, model {model_idx}.")
    return token_usage