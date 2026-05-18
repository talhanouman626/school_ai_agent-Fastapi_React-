import os
import warnings

os.environ["TOKENIZERS_PARALLELISM"]       = "false"
os.environ["TRANSFORMERS_VERBOSITY"]        = "error"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
warnings.filterwarnings("ignore")

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from config import EMBEDDING_MODEL, EMBEDDING_CACHE, FAISS_INDEX_PATH

print("📚 Loading documents...")
loader = DirectoryLoader(
    "school_data",
    glob="**/*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
    show_progress=False,
)
documents = loader.load()

if not documents:
    print("❌ No .md files found in school_data/ — aborting.")
    exit(1)

print(f"   ✅ {len(documents)} file(s) loaded.")

for doc in documents:
    for line in doc.page_content.splitlines():
        if "source_url:" in line:
            url = line.split("source_url:")[-1].strip().rstrip("-->").strip()
            doc.metadata["source_url"] = url
            break

print("✂️  Splitting into chunks...")
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)
chunks = splitter.split_documents(documents)
print(f"   ✅ {len(chunks)} chunks created.")

print("🧠 Building embeddings...")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
    cache_folder=EMBEDDING_CACHE,
)

print("💾 Saving FAISS index...")
vector_store = FAISS.from_documents(chunks, embeddings)
vector_store.save_local(FAISS_INDEX_PATH)

print()
print("✅ Done! Push these to GitHub:")
print(f"   📁 {FAISS_INDEX_PATH}/")
print(f"   📁 {EMBEDDING_CACHE}/   (optional)")
