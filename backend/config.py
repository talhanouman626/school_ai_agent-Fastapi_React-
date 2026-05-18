# ============================================================
# config.py — Saari constants ek jagah
# ============================================================

# ── Model Pool ────────────────────────────────────────────────
MODEL_POOL = [
    {
        "model_id":  "meta-llama/llama-4-scout-17b-16e-instruct",
        "tpd_limit": 500_000,
        "label":     "Llama 4 Scout",
    },
    {
        "model_id":  "llama-3.3-70b-versatile",
        "tpd_limit": 100_000,
        "label":     "Llama 3.3 70B",
    },
]

ROTATION_THRESHOLD = 0.90       # 90% pe next key/model

# ── Embedding Model ───────────────────────────────────────────
EMBEDDING_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_CACHE   = ".model_cache"
FAISS_INDEX_PATH  = "faiss_index"
TOP_K_RESULTS     = 5

# ── School Info ───────────────────────────────────────────────
SCHOOL_PHONE      = "0304-1111-647"
SCHOOL_WHATSAPP   = "https://wa.me/923041111647"
SCHOOL_WEBSITE    = "https://www.mgs.edu.pk/"
SCHOOL_MAP        = "https://www.mgs.edu.pk/contact-us.html"
SCHOOL_LOGO       = "https://cdn-icons-png.flaticon.com/512/4712/4712035.png"