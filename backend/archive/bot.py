import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from datetime import datetime
current_date = datetime.now().strftime("%d %B %Y")
# 1. Load Environment
load_dotenv()


# 2. Load School Data (Same as before)
def load_school_data(folder_path="school_data"):
    all_context = ""
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.endswith(".md"):
                with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                    all_context += f"\n\n=== {filename.upper()} ===\n{f.read()}"
    return all_context


# 3. Setup Model & Memory
model = ChatGroq(
    temperature=0.1,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Memory store (dictionary to keep history for different users if needed)
history_store = {}


def get_session_history(session_id: str):
    if session_id not in history_store:
        history_store[session_id] = ChatMessageHistory()
    return history_store[session_id]


# 4. Define the Chain (Prompt | Model | Parser)
context_data = load_school_data()

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

# Build the Chain using LCEL (LangChain Expression Language)
chain = prompt | model | StrOutputParser()

# Wrap with Message History for Memory
wrapped_chain = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

# 5. Execution Loop
session_id = "user_1"  # In production, this can be the user's unique ID
print("MGS Bot is Live! (Type 'exit' to quit)")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() == 'exit': break

    response = wrapped_chain.invoke(
        {"question": user_input},
        config={"configurable": {"session_id": session_id}}
    )

    print(f"\nBot: {response}") 