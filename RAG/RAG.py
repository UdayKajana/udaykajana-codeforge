from venv_manager import install_deps
install_deps(["openai", "chromadb", "pypdf", "tiktoken", "ipywidgets"])

# 📚 IMPORTS
import uuid
import textwrap
import sys
import subprocess
#----------------------------------------
from openai import OpenAI
from pypdf import PdfReader
#----------------------------------------
import chromadb

# 🔑 OPENAI CLIENT
OPENAI_API_KEY = ""
client = OpenAI( api_key= OPENAI_API_KEY)

# 🗂️ SELECT PDF FILE
def select_pdf_file():
    script = 'POSIX path of (choose file with prompt "Select a PDF file" of type {"pdf"})'
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        print("No file selected. Exiting.")
        sys.exit(1)
    return result.stdout.strip()

# 📄 LOAD PDF
def load_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

# ✂️ CHUNKER WITH OVERLAP
def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # move forward with overlap
        start += chunk_size - overlap
    return chunks

# 🧠 CREATE EMBEDDING
def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# 🗂️ CHROMADB SETUP
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(
    name="simple_rag"
)

# 📥 STORE CHUNKS
def add_chunks_to_chroma(chunks):
    for chunk in chunks:
        embedding = get_embedding(chunk)
        collection.add(
            ids=[str(uuid.uuid4())],
            documents=[chunk],
            embeddings=[embedding]
        )

    print(f"Stored {len(chunks)} chunks in ChromaDB.")


# 🔎 RETRIEVE DOCUMENTS
def retrieve(query, top_k=3):
    query_embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    docs = results["documents"][0]
    return docs

# 🤖 ASK QUESTION
def ask(query):
    docs = retrieve(query)
    context = "\n\n".join(docs)
    prompt = f"""
    You are a helpful RAG assistant.
    Answer ONLY from the provided context.
    If the answer is not in the context, say:
    "I could not find the answer in the document."
    Context:
    {context}
    Question:
    {query}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You answer questions using retrieved documents."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


pdf_path = select_pdf_file()
print(f"\nLoaded PDF: {pdf_path}")

# 🏗️ BUILD RAG PIPELINE
print("\nLoading PDF...")
text = load_pdf(pdf_path)
print("PDF loaded.")
print("\nChunking document...")
chunks = chunk_text(text, chunk_size=800, overlap=200)
print(f"Created {len(chunks)} chunks.")
print("\nGenerating embeddings and storing in ChromaDB...")
add_chunks_to_chroma(chunks)
print("\n✅ RAG Pipeline Ready")

# 💬 INTERACTIVE CHATBOT
print("\n🤖 Chatbot Ready")
print("Type 'exit' to stop.\n")
while True:
    query = input("You: ")
    if query.lower() == "exit":
        print("\nBot: Goodbye.")
        break
    answer = ask(query)
    print("\nBot:")
    print(textwrap.fill(answer, width=100))
    print("\n" + "=" * 100 + "\n")