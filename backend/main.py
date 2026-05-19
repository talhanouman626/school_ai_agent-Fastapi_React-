# ============================================================
# main.py — FastAPI Backend Server
#
# Endpoints:
#   GET  /health         → server alive check
#   POST /translate      → Urdu → English (frontend display ke liye)
#   POST /chat           → user message bhejo, jawab lo
#   POST /chat/clear     → session history clear karo
# ============================================================

import os
import logging
import warnings
import uuid
from contextlib import asynccontextmanager
from dotenv import load_dotenv

os.environ["TOKENIZERS_PARALLELISM"]        = "false"
os.environ["TRANSFORMERS_VERBOSITY"]         = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"]  = "1"
warnings.filterwarnings("ignore")

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory

from config import SCHOOL_PHONE, MODEL_POOL
from llm_manager import (
    load_api_keys,
    get_active_llm,
    record_token_usage,
    handle_rate_limit_error,
)
from vector_store import get_embeddings, load_vector_store
from prompt import prompt

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================
# Global State
# ============================================================
app_state = {
    "retriever":        None,
    "api_keys":         [],
    "token_usage":      {},
    "active_key_idx":   0,
    "active_model_idx": 0,
    "sessions":         {},
}

# ============================================================
# LIFESPAN
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🧠 Loading embeddings...")
    embeddings = get_embeddings()
    print("📚 Loading FAISS index...")
    app_state["retriever"] = load_vector_store(embeddings)
    print("🔑 Loading API keys...")
    app_state["api_keys"]  = load_api_keys()
    if not app_state["api_keys"]:
        raise RuntimeError("No API keys found. Add GROQ_API_KEY_1 to .env")
    print("✅ Backend ready!")
    yield
    print("🛑 Shutting down.")

app = FastAPI(title="MGS Campus Companion API", lifespan=lifespan)

# ============================================================
# CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://school-ai-agent-fastapi-react.vercel.app",
        "https://school-ai-agent-fastapi-react-1xkbkct9s.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# HELPERS
# ============================================================
def has_urdu_script(text: str) -> bool:
    return any('\u0600' <= ch <= '\u06FF' for ch in text)


def translate_to_english(llm, text: str) -> str:
    """Urdu → English. Fail hone pe original return karo."""
    try:
        result = llm.invoke([
            SystemMessage(content=(
                "Translate the following Urdu question to English. "
                "Output ONLY the English translation — no explanation, nothing else."
            )),
            HumanMessage(content=text),
        ])
        return result.content.strip() or text
    except Exception as ex:
        logger.error(f"[TRANSLATION ERROR] {ex}")
        return text

# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================
class ChatRequest(BaseModel):
    message:    str
    session_id: str | None = None

class ChatResponse(BaseModel):
    reply:            str
    session_id:       str
    model_used:       str
    translated_query: str

class ClearRequest(BaseModel):
    session_id: str

class TranslateRequest(BaseModel):
    text: str

class TranslateResponse(BaseModel):
    translated: str
    original:   str

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/health")
def health():
    return {
        "status":       "ok",
        "keys_loaded":  len(app_state["api_keys"]),
        "active_model": MODEL_POOL[app_state["active_model_idx"]]["label"],
    }


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    """
    Frontend ke liye — voice query English mein translate karo display ke liye.
    Sirf Urdu script hone pe translate hoga.
    """
    if not has_urdu_script(req.text):
        return TranslateResponse(translated=req.text, original=req.text)

    llm, ki, mi = get_active_llm(
        app_state["api_keys"],
        app_state["token_usage"],
        app_state["active_key_idx"],
        app_state["active_model_idx"],
    )
    app_state["active_key_idx"]   = ki
    app_state["active_model_idx"] = mi

    if llm is None:
        return TranslateResponse(translated=req.text, original=req.text)

    translated = translate_to_english(llm, req.text)
    return TranslateResponse(translated=translated, original=req.text)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # ── Session ───────────────────────────────────────────
    session_id = req.session_id or str(uuid.uuid4())
    if session_id not in app_state["sessions"]:
        app_state["sessions"][session_id] = ChatMessageHistory()
    history = app_state["sessions"][session_id]

    # ── LLM ───────────────────────────────────────────────
    llm, ki, mi = get_active_llm(
        app_state["api_keys"],
        app_state["token_usage"],
        app_state["active_key_idx"],
        app_state["active_model_idx"],
    )
    app_state["active_key_idx"]   = ki
    app_state["active_model_idx"] = mi

    if llm is None:
        raise HTTPException(
            status_code=429,
            detail="All API keys exhausted. Please try again tomorrow."
        )

    # ── Urdu → English translate (RAG ke liye) ───────────
    translated_query = req.message
    if has_urdu_script(req.message):
        translated_query = translate_to_english(llm, req.message)
        logger.error(f"[TRANSLATION] '{req.message}' → '{translated_query}'")

    # ── RAG ───────────────────────────────────────────────
    try:
        docs = app_state["retriever"].invoke(translated_query)
    except Exception as e:
        logger.error(f"Retriever error: {e}")
        raise HTTPException(status_code=500, detail="Knowledge base error.")

    context_parts = []
    for doc in docs:
        text = doc.page_content
        url  = doc.metadata.get("source_url", "")
        if url:
            text = f"source_url: {url}\n{text}"
        context_parts.append(text)
    context_text = "\n\n---\n\n".join(context_parts)

    # ── Chain ─────────────────────────────────────────────
    chain = prompt | llm | StrOutputParser()

    try:
        response = chain.invoke({
            "question": req.message,
            "context":  context_text,
            "history":  history.messages,
        })
    except Exception as e:
        err = str(e)
        if "429" in err or "rate_limit" in err.lower():
            app_state["token_usage"] = handle_rate_limit_error(
                app_state["token_usage"], ki, mi
            )
            raise HTTPException(status_code=429, detail="Rate limit hit. Please retry.")
        logger.error(f"LLM error [{session_id}]: {e}")
        raise HTTPException(status_code=500, detail="AI response error.")

    # ── History update ────────────────────────────────────
    history.add_user_message(req.message)
    history.add_ai_message(response)

    # ── Token usage ───────────────────────────────────────
    approx = int((len(req.message.split()) + len(response.split())) * 1.3)
    app_state["token_usage"] = record_token_usage(
        app_state["token_usage"], ki, mi, approx
    )

    return ChatResponse(
        reply=response,
        session_id=session_id,
        model_used=MODEL_POOL[mi]["label"],
        translated_query=translated_query,
    )


@app.post("/chat/clear")
def clear_session(req: ClearRequest):
    if req.session_id in app_state["sessions"]:
        del app_state["sessions"][req.session_id]
    return {"status": "cleared", "session_id": req.session_id}