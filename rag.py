#!/usr/bin/env python3

import os, sys, io, pickle
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import faiss
from sentence_transformers import SentenceTransformer
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("pdf_rag")

# Constants
FILES_DIR = os.path.join(os.path.dirname(__file__), "files")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "index.faiss")
DOCS_PATH = os.path.join(os.path.dirname(__file__), "docs.pkl")

# Embedding model
MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def parse_pdf(file_path: str) -> list[tuple[str, str]]:
    """Extract text with OCR fallback and chunked normalization."""
    chunks = []
    try:
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc):
            text = page.get_text().strip()
            if not text:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img).strip()

            if text:
                text = text.replace("\n", " ").lower()
                for i in range(0, len(text), 1000):
                    chunk = text[i : i + 1000].strip()
                    if chunk:
                        label = f"{os.path.basename(file_path)} [Page {page_num + 1}]"
                        chunks.append((label, chunk))
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
    return chunks


def build_index() -> str:
    """Build FAISS index from PDFs in ./files directory."""
    if not os.path.exists(FILES_DIR):
        return "Missing 'files' directory."

    docs = []
    for fname in os.listdir(FILES_DIR):
        if fname.lower().endswith(".pdf"):
            path = os.path.join(FILES_DIR, fname)
            docs.extend(parse_pdf(path))

    if not docs:
        return "No extractable text found."

    texts = [text for _, text in docs]
    embeddings = MODEL.encode(texts, convert_to_numpy=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    with open(DOCS_PATH, "wb") as f:
        pickle.dump(docs, f)
    faiss.write_index(index, INDEX_PATH)

    return f"Indexed {len(docs)} chunks from {len(set(name for name, _ in docs))} PDFs."


def search_index(query: str, top_k: int = 5) -> str:
    """Semantic search across the indexed document chunks."""
    if not os.path.exists(INDEX_PATH) or not os.path.exists(DOCS_PATH):
        return "Index not found. Please run `rebuild_index()`."

    try:
        index = faiss.read_index(INDEX_PATH)
        with open(DOCS_PATH, "rb") as f:
            docs = pickle.load(f)

        query_vec = MODEL.encode([query.lower()], convert_to_numpy=True)
        D, I = index.search(query_vec, top_k)

        results = []
        for i in I[0]:
            if 0 <= i < len(docs):
                label, chunk = docs[i]
                results.append(f"Match in {label}:\n{chunk.strip()[:1000]}")

        return "\n---\n".join(results) if results else "No relevant content found."
    except Exception as e:
        print(f"Search failed: {e}", file=sys.stderr)
        return "Search failed."


@mcp.tool()
async def rebuild_index() -> str:
    """Rebuild the index from PDF files in ./files."""
    return build_index()


@mcp.tool()
async def query_pdfs(query: str) -> str:
    """Search the indexed PDFs for a given query."""
    try:
        return search_index(query)
    except Exception as e:
        print(f"Query error: {e}", file=sys.stderr)
        return "Query failed."


if __name__ == "__main__":
    mcp.run(transport="stdio")
