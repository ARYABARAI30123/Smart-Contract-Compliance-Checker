import os
import pdfplumber
import pytesseract
from PIL import Image
from docx import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain_groq import ChatGroq

#  Set Groq API Key (Ensure this is correctly set in .env)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
#  Initialize LLM with Groq (Using Mixtral-8x7b)
llm = ChatGroq(api_key=GROQ_API_KEY, model_name="mixtral-8x7b-32768")

# Set Tesseract path (Windows users)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text(file_path):
    """Extracts text from PDFs, Images, Word Docs, and TXT files."""
    ext = file_path.split(".")[-1].lower()

    try:
        if ext == "pdf":
            with pdfplumber.open(file_path) as pdf:
                return " ".join([page.extract_text() for page in pdf.pages if page.extract_text()]) or "Error: No text found in PDF."
        elif ext in ["jpg", "jpeg", "png"]:
            return pytesseract.image_to_string(Image.open(file_path)).strip() or "Error: No text detected in image."
        elif ext == "docx":
            return "\n".join([para.text for para in Document(file_path).paragraphs]).strip() or "Error: No text found in DOCX."
        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read().strip() or "Error: No text found in TXT."
        else:
            return "Error: Unsupported file format."
    except Exception as e:
        return f"Error processing {ext.upper()}: {str(e)}"

def analyze_contract(file_path):
    """Processes the contract and finds key compliance issues."""
    contract_text = extract_text(file_path)
    if contract_text.startswith("Error:"):
        return contract_text  # If extraction failed, return error.

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    texts = text_splitter.split_text(contract_text)

    # Load or Create FAISS Vector Store
    vector_store_path = "faiss_contract_index"
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")

    if os.path.exists(vector_store_path):
        try:
            vector_store = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)
        except:
            vector_store = FAISS.from_texts(texts, embeddings)
            vector_store.save_local(vector_store_path)
    else:
        vector_store = FAISS.from_texts(texts, embeddings)
        vector_store.save_local(vector_store_path)

    docs = vector_store.similarity_search("Contract analysis", k=5)
    qa_chain = load_qa_chain(llm, chain_type="stuff")

    query = """
    Analyze this contract and summarize:
    1️⃣ **Major Risks**: Identify financial, legal, or operational risks.
    2️⃣ **Compliance Issues**: Highlight missing or vague legal details.
    3️⃣ **Unfair Terms**: Point out clauses that create imbalance.
    
    Use bullet points. If no risks exist, highlight potential loopholes.
    """

    response = qa_chain.run({"input_documents": docs, "question": query})
    return format_response(response)

def format_response(response):
    """Formats the AI model's output."""
    if "No major issues found" in response:
        return "**No critical issues found, but consider improving clarity and legal protections.**"
    return response
