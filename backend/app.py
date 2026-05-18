import streamlit as st
import os
import uuid
import logging
import warnings
from dotenv import load_dotenv
from datetime import datetime

os.environ["TOKENIZERS_PARALLELISM"]       = "false"
os.environ["TRANSFORMERS_VERBOSITY"]        = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
warnings.filterwarnings("ignore")

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

from config import SCHOOL_LOGO, SCHOOL_WEBSITE, SCHOOL_MAP, SCHOOL_WHATSAPP
from prompt import prompt
from llm_manager import load_api_keys, init_token_tracker, get_active_llm, handle_rate_limit_error, record_token_usage
from vector_store import get_embeddings, load_vector_store

load_dotenv()

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(level=logging.ERROR, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ============================================================
# PAGE CONFIG & STYLES
# ============================================================
st.set_page_config(page_title="Campus Companion AI", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    /* ── Sidebar ── */
    [data-testid="stSidebar"] { background-color: #111111; color: white; }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #E0E0E0 !important; margin-bottom: 5px; }
    .stImage > img { margin-top: -30px; padding-bottom: 10px; }

    /* ── Sidebar Clear button ── */
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 5px !important;
        background-color: #262626 !important;
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
        width: 100% !important;
        font-weight: bold !important;
        height: 35px !important;
        font-size: 14px !important;
        text-align: center !important;
        white-space: nowrap !important;
    }

    /* ── Layout ── */
    .block-container { max-width: 950px; padding-top: 1.5rem; }
    [data-testid="stSidebar"] a {
        text-decoration: none; color: #4da3ff !important;
        display: block; padding: 5px 0px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Topic card buttons — target by data-testid ── */
    [data-testid="stMainBlockContainer"] .stButton > button {
        background-color: #161b22 !important;
        color: #c9d1d9 !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        height: 80px !important;
        font-size: 13px !important;
        font-weight: normal !important;
        text-align: left !important;
        padding: 12px 14px !important;
        white-space: normal !important;
        line-height: 1.5 !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stMainBlockContainer"] .stButton > button:hover {
        background-color: #21262d !important;
        border-color: #58a6ff !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# SUGGESTED TOPICS
# ============================================================
SUGGESTED_TOPICS = [
    ("📋", "Fee details?"),
    ("🎓", "Admission process?"),
    ("⏰", "School timings?"),
    ("📍", "School location?"),
    ("🏫", "Tell me about MGS"),
    ("📜", "School policy?"),
    ("🎨", "What is life like at MGS?"),
    ("📞", "Contact?"),
]

# ============================================================
# SESSION ID
# ============================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "suggested_query" not in st.session_state:
    st.session_state.suggested_query = None

if "chat_started" not in st.session_state:
    st.session_state.chat_started = False

msgs = StreamlitChatMessageHistory(key="chat_messages")

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image(SCHOOL_LOGO, width=100)
    st.markdown("### **Campus Dashboard**")
    st.markdown("---")

    st.markdown("📣 **Current Status**")
    st.success("🟢 Campus is Open")
    st.info("🕒 Today's Timing: 08:00 AM - 01:45 PM")

    st.markdown("---")
    st.markdown("🔗 **Quick Access**")
    st.markdown(f"🌐 [Official Website]({SCHOOL_WEBSITE})")
    st.markdown(f"📍 [Location Map]({SCHOOL_MAP})")
    st.markdown(f"💬 [WhatsApp Support]({SCHOOL_WHATSAPP})")

    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        msgs.clear()
        st.session_state.chat_started = False
        st.rerun()

    st.caption(f"Sync Date: {datetime.now().strftime('%d %B %Y')}")
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")

# ============================================================
# STARTUP
# ============================================================
st.title("🤖 Campus Companion AI")
st.markdown("---")

api_keys = load_api_keys()
if not api_keys:
    st.error("⚠️ No API keys found. Add GROQ_API_KEY_1 (or GROQ_API_KEY) to your .env file.")
    st.stop()

init_token_tracker()

if "app_ready" not in st.session_state:
    with st.status("⚡ Starting up Campus Companion AI...", expanded=True) as status:
        st.write("🧠 Loading AI model...")
        embeddings = get_embeddings()
        st.write("📚 Connecting to knowledge base...")
        retriever  = load_vector_store(embeddings)
        st.write("✅ All systems ready!")
        status.update(label="✅ Campus Companion AI is Ready!", state="complete", expanded=False)
        st.session_state.app_ready = True
else:
    embeddings = get_embeddings()
    retriever  = load_vector_store(embeddings)

# ============================================================
# SUGGESTED TOPICS — sirf jab chat shuru nahi hui
# ============================================================
if not st.session_state.chat_started:
    st.markdown("#### 💡 What would you like to know?")
    cols = st.columns(4)
    for i, (icon, question) in enumerate(SUGGESTED_TOPICS):
        with cols[i % 4]:
            if st.button(f"{icon}\n\n{question}", key=f"suggest_{i}", use_container_width=True):
                st.session_state.suggested_query = question
                st.session_state.chat_started = True
                st.rerun()

# ============================================================
# CHAT DISPLAY
# ============================================================
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

# ============================================================
# SPEECH TO TEXT
# st.components.v1.html iframe mein JS execute hoti hai —
# wahan se parent frame mein fixed mic button inject karte hain
# taake scroll pe bhi nazar aaye aur click bhi kaam kare
# ============================================================
st.components.v1.html("""
<script>
(function() {
  // Is script ko sirf ek baar chalao
  if (window.parent.document.getElementById('mic-fixed')) return;

  const p = window.parent.document;

  // ── CSS inject karo parent mein ──────────────────────────
  const style = p.createElement('style');
  style.textContent = `
    #mic-fixed {
      position: fixed;
      bottom: 14px;
      right: 72px;
      z-index: 999999;
      width: 38px; height: 38px;
      border-radius: 50%;
      border: 1.5px solid #555;
      background: #1a1a2e;
      font-size: 17px;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 2px 8px rgba(0,0,0,0.5);
      transition: border-color .2s, background .2s;
      user-select: none;
    }
    #mic-fixed:hover { border-color: #58a6ff; background: #21262d; }
    #mic-fixed.on {
      border-color: #ff4b4b !important;
      background: #2d1010 !important;
      animation: micpulse 1s infinite;
    }
    @keyframes micpulse {
      0%   { box-shadow: 0 0 0 0   rgba(255,75,75,.5); }
      70%  { box-shadow: 0 0 0 9px rgba(255,75,75,0);  }
      100% { box-shadow: 0 0 0 0   rgba(255,75,75,0);  }
    }
    #mic-tip {
      position: fixed;
      bottom: 62px; right: 52px;
      z-index: 999999;
      background: #1e1e2e;
      border: 1px solid #333;
      border-radius: 8px;
      padding: 5px 10px;
      font-size: 11px;
      color: #ccc;
      font-family: sans-serif;
      max-width: 230px;
      display: none;
      line-height: 1.5;
      box-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }
    #mic-tip.show { display: block; }
    #mic-tip.live { color:#ff6b6b; border-color:#ff4b4b; }
    #mic-tip.ok   { color:#3fb950; border-color:#3fb950; }
    #mic-tip.err  { color:#f0883e; border-color:#f0883e; }
  `;
  p.head.appendChild(style);

  // ── Mic button + tooltip DOM banao ───────────────────────
  const mic = p.createElement('div');
  mic.id = 'mic-fixed';
  mic.textContent = '🎤';
  p.body.appendChild(mic);

  const tip = p.createElement('div');
  tip.id = 'mic-tip';
  p.body.appendChild(tip);

  // ── Status helper ─────────────────────────────────────────
  function showTip(msg, cls, ms) {
    tip.textContent = msg;
    tip.className   = 'show ' + (cls || '');
    if (ms) setTimeout(() => { tip.className = ''; }, ms);
  }

  // ── Speech Recognition ────────────────────────────────────
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    mic.textContent  = '🚫';
    mic.title        = 'Chrome use karein';
    mic.style.opacity = '0.4';
    mic.style.cursor  = 'not-allowed';
    return;
  }

  const rec = new SR();
  rec.lang           = 'ur-PK';   // Urdu primary, English bhi kaam karta hai
  rec.interimResults = true;
  rec.continuous     = false;

  let going = false, final_ = '';

  mic.addEventListener('click', () => going ? rec.stop() : rec.start());

  rec.onstart = () => {
    going = true; final_ = '';
    mic.classList.add('on');
    mic.textContent = '⏹️';
    showTip('🔴 Sun raha hoon... (dobara click = band)', 'live');
  };

  rec.onresult = e => {
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) final_ += e.results[i][0].transcript;
      else interim += e.results[i][0].transcript;
    }
    showTip('📝 ' + (final_ || interim), 'live');
  };

  rec.onend = () => {
    going = false;
    mic.classList.remove('on');
    mic.textContent = '🎤';

    if (!final_.trim()) { tip.className = ''; return; }

    // Parent frame ke chat textarea mein inject karo
    const ta = p.querySelector('[data-testid="stChatInput"] textarea');
    if (ta) {
      Object.getOwnPropertyDescriptor(
        window.parent.HTMLTextAreaElement.prototype, 'value'
      ).set.call(ta, final_.trim());
      ta.dispatchEvent(new Event('input', { bubbles: true }));
      ta.focus();
      setTimeout(() => {
        ta.dispatchEvent(new KeyboardEvent('keydown', {
          key: 'Enter', code: 'Enter', keyCode: 13,
          which: 13, bubbles: true, cancelable: true
        }));
        showTip('✅ ' + final_.trim(), 'ok', 3000);
      }, 250);
    } else {
      showTip('⚠️ Paste karein: ' + final_.trim(), 'err', 5000);
    }
  };

  rec.onerror = e => {
    going = false;
    mic.classList.remove('on');
    mic.textContent = '🎤';
    const m = {
      'not-allowed': '🚫 Mic Allow karein browser mein',
      'no-speech':   '🔇 Awaaz nahi aayi — dobara try karein',
      'network':     '🌐 Network error',
    };
    showTip(m[e.error] || '❌ ' + e.error, 'err', 4000);
  };
})();
</script>
""", height=0)

typed_query = st.chat_input("How can I help you today?")
user_query = typed_query
if st.session_state.suggested_query:
    user_query = st.session_state.suggested_query
    st.session_state.suggested_query = None

# ============================================================
# URDU → ENGLISH QUERY TRANSLATION (FAISS ke liye)
# FAISS index English/Roman Urdu mein hai — pure Urdu script
# queries se relevant docs nahi milte. Isliye query ko pehle
# English mein translate karo, phir FAISS mein search karo.
# User ko original query hi dikhti hai — translate sirf retrieval ke liye.
# ============================================================
def has_urdu_script(text: str) -> bool:
    """Check karo ke text mein Urdu/Arabic script hai ya nahi."""
    for ch in text:
        if '\u0600' <= ch <= '\u06FF':  # Arabic/Urdu Unicode block
            return True
    return False


def translate_query_for_retrieval(query: str, llm) -> str:
    """
    Agar query Urdu script mein hai to English mein translate karo.
    Sirf retrieval ke liye — user ko original dikhti hai.
    """
    if not has_urdu_script(query):
        return query  # Roman Urdu ya English — as-is

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        msgs_translate = [
            SystemMessage(content=(
                "You are a translator. Translate the following Urdu question to English. "
                "Output ONLY the English translation — no explanation, no extra text."
            )),
            HumanMessage(content=query),
        ]
        result = llm.invoke(msgs_translate)
        translated = result.content.strip()
        logger.error(f"[TRANSLATION] '{query}' → '{translated}'")
        return translated if translated else query
    except Exception as ex:
        logger.error(f"[TRANSLATION ERROR] {ex}")
        return query  # Fallback — original query use karo


# ============================================================
# HANDLE INPUT
# ============================================================
if user_query:
    st.session_state.chat_started = True
    st.chat_message("human").write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                llm = get_active_llm(api_keys)
                if llm is None:
                    st.error("⚠️ All API keys have reached their daily limit. Please try again tomorrow.")
                    st.stop()

                # Urdu script query → English translate karo FAISS ke liye
                retrieval_query = translate_query_for_retrieval(user_query, llm)

                relevant_docs = retriever.invoke(retrieval_query)
                context_parts = []
                for doc in relevant_docs:
                    text = doc.page_content
                    url  = doc.metadata.get("source_url", "")
                    if url:
                        text = f"source_url: {url}\n{text}"
                    context_parts.append(text)
                context_text = "\n\n---\n\n".join(context_parts)

                chain = (prompt | llm | StrOutputParser())
                chain_with_history = RunnableWithMessageHistory(
                    chain,
                    lambda session_id: msgs,
                    input_messages_key="question",
                    history_messages_key="history",
                )

                response = chain_with_history.invoke(
                    {"question": user_query, "context": context_text},
                    config={"configurable": {"session_id": st.session_state.session_id}},
                )
                st.write(response)

                approx_tokens = int((len(user_query.split()) + len(response.split())) * 1.3)
                record_token_usage(
                    st.session_state.active_key_idx,
                    st.session_state.active_model_idx,
                    approx_tokens,
                )

            except Exception as e:
                err_str = str(e)

                if "429" in err_str or "rate_limit" in err_str.lower():
                    handle_rate_limit_error()
                    logger.error(f"Rate limit [{st.session_state.session_id}]: {e}")
                    st.warning("⚡ Switching to next available key — please send your message again.")

                elif "connection" in err_str.lower():
                    logger.error(f"Connection [{st.session_state.session_id}]: {e}")
                    st.error("🔌 Connection error. Please check your internet and try again.")

                elif "timeout" in err_str.lower():
                    logger.error(f"Timeout [{st.session_state.session_id}]: {e}")
                    st.error("⏱️ Request timed out. Please try again.")

                else:
                    logger.error(f"Error [{st.session_state.session_id}]: {e}")
                    st.error("⚠️ Something went wrong. Please try again or contact the school: **0304-1111-647**")