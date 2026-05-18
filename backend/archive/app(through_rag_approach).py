import streamlit as st
import os
import uuid
import logging
from dotenv import load_dotenv
from datetime import datetime

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

# RAG imports
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================
# PAGE CONFIG & STYLES
# ============================================================
st.set_page_config(page_title="Campus Companion AI", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #111111; color: white; }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #E0E0E0 !important; margin-bottom: 5px; }
    .stImage > img { margin-top: -30px; padding-bottom: 10px; }
    .stButton button {
        border-radius: 5px; background-color: #262626;
        color: #ff4b4b; border: 1px solid #ff4b4b;
        width: 100%; font-weight: bold; height: 35px;
    }
    .block-container { max-width: 950px; padding-top: 1.5rem; }
    [data-testid="stSidebar"] a {
        text-decoration: none; color: #4da3ff !important;
        display: block; padding: 5px 0px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

load_dotenv()

# ============================================================
# RAG — AUTOMATIC CHANGE DETECTION + VECTOR STORE
#
# Problem jo solve ki:
#   Production mein manually .chromadb_cache/ delete karna
#   possible nahi — koi kare bhi kyun?
#
# Solution — Hash-based auto detection:
#   1. Saari .md files ka content read karo
#   2. Sab ka milake ek "fingerprint" (hash) banao
#   3. Yeh hash .chromadb_cache/content_hash.txt mein save karo
#   4. Agli baar app chale → naya hash banao → purane se milao
#      - Same hash → files nahi badli → cached DB use karo (fast)
#      - Alag hash → koi file badli → DB delete karo, rebuild karo
#
# Koi manual kaam nahi — automatic production-ready system
# ============================================================

import hashlib
import shutil


def compute_folder_hash(folder_path: str) -> str:
    """
    Saari .md files ka content milake ek unique fingerprint banata hai.
    Agar koi bhi file badli — naya number aayega.
    """
    hasher = hashlib.md5()
    if not os.path.exists(folder_path):
        return ""
    for fname in sorted(os.listdir(folder_path)):        # sorted → consistent order
        if fname.endswith(".md"):
            fpath = os.path.join(folder_path, fname)
            with open(fpath, "rb") as f:
                hasher.update(f.read())
    return hasher.hexdigest()                            # e.g. "a3f8c2d1..."


CHROMA_DIR  = ".chromadb_cache"
HASH_FILE   = os.path.join(CHROMA_DIR, "content_hash.txt")


def get_saved_hash() -> str:
    """Disk pe jo hash save tha woh wapas laata hai. Nahi mila → khali string."""
    try:
        with open(HASH_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def save_current_hash(hash_value: str):
    """Naya hash disk pe save karta hai future comparison ke liye."""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    with open(HASH_FILE, "w") as f:
        f.write(hash_value)


@st.cache_resource(show_spinner="📚 Building knowledge base... (first time only)")
def build_vector_store(folder_path: str = "school_data"):
    """
    .md files detect karta hai, zaroorat parne par rebuild karta hai.
    Production mein fully automatic — koi manual step nahi.
    """

    # ── Step 1: Files ka fingerprint banao ────────────────────
    current_hash = compute_folder_hash(folder_path)
    saved_hash   = get_saved_hash()

    # ── Step 2: Compare karo ──────────────────────────────────
    if current_hash != saved_hash:
        # Koi file badli ya nayi aai → purana DB saaf karo
        logger.error(f"Content changed (old={saved_hash[:8]}, new={current_hash[:8]}) — rebuilding.")
        if os.path.exists(CHROMA_DIR):
            shutil.rmtree(CHROMA_DIR)   # poora folder delete, fresh start

    # ── Step 3: Agar DB pehle se bana hai → sirf load karo ───
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )

    if os.path.exists(CHROMA_DIR) and current_hash == saved_hash:
        # Fast path — kuch nahi badla, DB as-is use karo
        vector_store = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings,
        )
        return vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},
        )

    # ── Step 4: Files load karo (sirf rebuild pe aata hai) ───
    loader = DirectoryLoader(
        folder_path,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=False,
    )
    documents = loader.load()

    if not documents:
        st.error(f"No .md files found in '{folder_path}/'. Please contact the admin.")
        st.stop()

    # source_url metadata extract karo
    for doc in documents:
        for line in doc.page_content.splitlines():
            if "source_url:" in line:
                url = line.split("source_url:")[-1].strip().rstrip("-->").strip()
                doc.metadata["source_url"] = url
                break

    # ── Step 5: Chunks banao ──────────────────────────────────
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
    chunks = splitter.split_documents(documents)

    # ── Step 6: ChromaDB banao aur disk pe save karo ─────────
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )

    # ── Step 7: Naya hash save karo ───────────────────────────
    # Agli baar yahi hash se compare hoga
    save_current_hash(current_hash)

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )


# ============================================================
# SESSION ID — Unique per browser tab
# ============================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

msgs = StreamlitChatMessageHistory(key="chat_messages")

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100)
    st.markdown("### **Campus Dashboard**")
    st.markdown("---")

    st.markdown("📣 **Current Status**")
    st.success("🟢 Campus is Open")
    st.info("🕒 Today's Timing: 08:00 AM - 01:45 PM")

    st.markdown("---")
    st.markdown("🔗 **Quick Access**")
    st.markdown("🌐 [Official Website](https://www.mgs.edu.pk/)")
    st.markdown("📍 [Location Map](https://www.mgs.edu.pk/contact-us.html)")
    st.markdown("💬 [WhatsApp Support](https://wa.me/923041111647)")

    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        msgs.clear()
        st.rerun()

    st.caption(f"Sync Date: {datetime.now().strftime('%d %B %Y')}")
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")

# ============================================================
# MAIN INTERFACE
# ============================================================
st.title("🤖 Campus Companion AI")
st.markdown("---")

if not os.getenv("GROQ_API_KEY"):
    st.error("⚠️ API Key is missing. Please contact the admin.")
    st.stop()

# Vector store build (cached — sirf pehli baar slow hoga)
retriever = build_vector_store("../school_data")

# LLM
model = ChatGroq(
    temperature=0.1,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY"),
)

current_date = datetime.now().strftime("%d %B %Y")

# ============================================================
# PROMPT — {context} ab dynamically aata hai har sawaal pe
# Poori data ek baar nahi, sirf relevant 5 chunks
# ============================================================
prompt = ChatPromptTemplate.from_messages([
    ("system", f"""You are 'Campus Companion AI', a strictly factual school assistant for MGS (Message Grammar School), Lahore.

STRICT IDENTITY RULES:
1. You do NOT know who you are chatting with — never assume their role.
2. Only mention staff/owner names if they appear in the CONTEXT below.

LANGUAGE RULES:
- Default: English. Switch to Urdu/Roman Urdu only if the user writes in it first.
- Use Markdown tables for fees and timings.

QUANTITY & COUNTING RULES (VERY IMPORTANT):
- If the user specifies a number, follow it EXACTLY. No more, no less.
- "sirf 1 person" → give EXACTLY 1. "top 3 fees" → give EXACTLY 3.
- Count BEFORE replying. Remove extras if needed.
- Words like "sirf", "only", "ek", "do", "teen" are hard quantity limits.

SOURCE LINK RULES:
- If CONTEXT has a line "source_url: https://...", use that URL.
- End your answer with: "🔗 More info: <URL>"
- Never make up URLs.

ACCURACY:
- Current date: {current_date}
- ONLY use info from CONTEXT below. Never use your general training knowledge.
- If answer not in CONTEXT: "Yeh info available nahi. Call karein: 0304-1111-647"

CONTEXT (relevant school data for this question only):
{{context}}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

chain = (prompt | model | StrOutputParser())

chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: msgs,
    input_messages_key="question",
    history_messages_key="history",
)

# Display existing chat
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

# Handle new input
if user_query := st.chat_input("How can I help you today?"):
    st.chat_message("human").write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                # RAG Step: sawaal → relevant chunks dhundho
                relevant_docs = retriever.invoke(user_query)

                # Chunks + source URLs ko ek string mein jodo
                context_parts = []
                for doc in relevant_docs:
                    text = doc.page_content
                    url  = doc.metadata.get("source_url", "")
                    if url:
                        text = f"source_url: {url}\n{text}"
                    context_parts.append(text)

                context_text = "\n\n---\n\n".join(context_parts)

                # LLM ko sirf yeh relevant context do
                response = chain_with_history.invoke(
                    {
                        "question": user_query,
                        "context":  context_text,
                    },
                    config={"configurable": {"session_id": st.session_state.session_id}},
                )
                st.write(response)

            except ConnectionError as e:
                logger.error(f"Connection [{st.session_state.session_id}]: {e}")
                st.error("🔌 Connection error. Please check your internet and try again.")

            except TimeoutError as e:
                logger.error(f"Timeout [{st.session_state.session_id}]: {e}")
                st.error("⏱️ Request timed out. Please try again.")

            except Exception as e:
                logger.error(f"Error [{st.session_state.session_id}]: {e}")
                st.error(
                    "⚠️ Something went wrong. Please try again or contact the school directly: "
                    "**0304-1111-647**"
                )