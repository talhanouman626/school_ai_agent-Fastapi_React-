# ============================================================
# vector_store.py — Embeddings + FAISS load (FastAPI version)
# st.cache_resource hata diya — FastAPI mein yeh kaam nahi karta
# Caching main.py mein lifespan se hogi
# ============================================================
import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL, EMBEDDING_CACHE, FAISS_INDEX_PATH, TOP_K_RESULTS


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
        cache_folder=EMBEDDING_CACHE,
    )


def load_vector_store(embeddings: HuggingFaceEmbeddings):
    if not os.path.exists(FAISS_INDEX_PATH):
        raise FileNotFoundError(
            f"faiss_index/ not found. Run build_index.py first."
        )
    vector_store = FAISS.load_local(
        FAISS_INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K_RESULTS},
    )