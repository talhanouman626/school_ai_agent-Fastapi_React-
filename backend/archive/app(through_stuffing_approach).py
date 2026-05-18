import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

# --- 1. Page Configuration ---
# Name updated to 'Campus Companion AI'
st.set_page_config(page_title="Campus Companion AI", page_icon="🤖", layout="wide")

# Professional UI Styling (Fixed Spacing & Dark Dashboard)
st.markdown("""
    <style>
    /* Dark Theme Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111111;
        color: white;
    }

    /* Global Sidebar Text Color */
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #E0E0E0 !important;
        margin-bottom: 5px;
    }

    /* Logo Styling */
    .stImage > img {
        margin-top: -30px;
        padding-bottom: 10px;
    }

    /* Professional Button in Sidebar */
    .stButton button {
        border-radius: 5px;
        background-color: #262626;
        color: #ff4b4b;
        border: 1px solid #ff4b4b;
        width: 100%;
        font-weight: bold;
        height: 35px;
    }

    /* Removing unnecessary scroll and fixing main area */
    .block-container {
        max-width: 950px;
        padding-top: 1.5rem;
    }

    /* Fixed spacing for sidebar icons */
    [data-testid="stSidebar"] a {
        text-decoration: none;
        color: #4da3ff !important;
        display: block;
        padding: 5px 0px;
    }

    /* Hide default Streamlit header/footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Backend Functions ---
load_dotenv()


def load_school_data(folder_path="school_data"):
    """Reads school information from modular markdown files"""
    all_context = ""
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.endswith(".md"):
                try:
                    with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                        section_name = filename.replace('.md', '').upper()
                        all_context += f"\n\n=== SECTION: {section_name} ===\n{f.read()}"
                except Exception as e:
                    st.error(f"Error: {e}")
    return all_context


# Initialize Chat History for Memory
msgs = StreamlitChatMessageHistory(key="chat_messages")

# --- 3. Sidebar (Professional Dashboard) ---
with st.sidebar:
    # Logo Placement
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100)
    st.markdown("### **Campus Dashboard**")
    st.markdown("---")

    # Clean Status Section
    st.markdown("📣 **Current Status**")
    st.success("🟢 Campus is Open")
    st.info("🕒 Today's Timing: 08:00 AM - 01:45 PM")

    st.markdown("---")

    # Clean Quick Access
    st.markdown("🔗 **Quick Access**")
    st.markdown("🌐 [Official Website](https://www.mgs.edu.pk/)")
    st.markdown("📍 [Location Map](https://www.mgs.edu.pk/contact)")
    st.markdown("💬 [Support Chat](https://wa.me/92300XXXXXXX)")

    st.markdown("---")

    # Action Button
    if st.button("🗑️ Clear Chat History"):
        msgs.clear()
        st.rerun()

    st.caption(f"Sync Date: {datetime.now().strftime('%d %B %Y')}")

# --- 4. Main Chat Interface ---
st.title("🤖 Campus Companion AI")
st.markdown("---")

# --- 5. AI Engine Setup ---
if not os.getenv("GROQ_API_KEY"):
    st.error("API Key Missing in Environment!")
    st.stop()

# Using high-performance Llama model
model = ChatGroq(
    temperature=0.1,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

context_data = load_school_data()
current_date = datetime.now().strftime("%d %B %Y")

# Updated System Prompt for 'Campus Companion' persona
# System prompt ko mazeed dynamic aur strict banaya gaya hai
prompt = ChatPromptTemplate.from_messages([
    ("system", f"""You are 'Campus Companion AI', a strictly factual school assistant. 

    STRICT IDENTITY RULES:
    1. **Anonymous Interaction**: You do NOT know the name or identity of the person you are chatting with. 
    2. **No Assumptions**: Never call the user 'Owner', 'Principal'. Even if they ask "Who am I?", reply that you are an AI and don't have access to their personal identity.
    3. **Data Bound**: Only talk about school staff or owners if their names are explicitly mentioned in the SECTION: GENERAL data. If not found, say you don't know.

    OPERATIONAL RULES:
    - Default Language: English. Switch to Urdu/Roman Urdu only if the user does.
    - Format: Use Markdown Tables for timings and fees.
    - Accuracy: Information is current as of {current_date}.

    CAMPUS DATA:
    {context_data}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

# Build Chain (LCEL)
chain = (prompt | model | StrOutputParser())

# Wrap with Message History for Memory support
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: msgs,
    input_messages_key="question",
    history_messages_key="history",
)

# Display Session Messages
for msg in msgs.messages:
    st.chat_message(msg.type).write(msg.content)

# Handle New User Input
if user_query := st.chat_input("How can I help you today?"):
    st.chat_message("human").write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing records..."):
            try:
                response = chain_with_history.invoke(
                    {"question": user_query},
                    config={"configurable": {"session_id": "campus_session"}}
                )
                st.write(response)
            except Exception as e:
                st.error(f"Execution Error: {e}")