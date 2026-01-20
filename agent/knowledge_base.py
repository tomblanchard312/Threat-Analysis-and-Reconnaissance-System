#!/usr/bin/env python3
"""
Knowledge Base System - RAG (Retrieval Augmented Generation) for HTB Pentest Agent
Allows ingesting books, PDFs, and documents to augment model responses.
"""

import json
import os
import re
import pickle
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import numpy as np

# TF-IDF for lightweight retrieval (no GPU/large models needed)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# PDF parsing
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

# Alternative PDF parsing
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class KnowledgeBase:
    """
    A lightweight RAG system using TF-IDF for retrieval.
    Designed to work offline with minimal dependencies.
    """

    def __init__(self, storage_dir: str):
        """
        Initialize the knowledge base.

        Args:
            storage_dir: Directory to store index and documents
        """
        self.storage_dir = storage_dir
        self.index_file = os.path.join(storage_dir, "kb_index.pkl")
        self.metadata_file = os.path.join(storage_dir, "kb_metadata.json")
        self.chunks_file = os.path.join(storage_dir, "kb_chunks.json")

        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)

        # Load existing data
        self.metadata = self._load_metadata()
        self.chunks = self._load_chunks()
        self.vectorizer = None
        self.tfidf_matrix = None

        # Load index if exists
        self._load_index()

    def _load_metadata(self) -> Dict:
        """Load metadata about indexed documents."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "documents": [],
            "total_chunks": 0,
            "last_updated": None,
            "version": "1.0"
        }

    def _save_metadata(self):
        """Save metadata."""
        self.metadata["last_updated"] = datetime.now().isoformat()
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)

    def _load_chunks(self) -> List[Dict]:
        """Load text chunks."""
        if os.path.exists(self.chunks_file):
            try:
                with open(self.chunks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []

    def _save_chunks(self):
        """Save text chunks."""
        with open(self.chunks_file, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f)

    def _load_index(self):
        """Load TF-IDF index from disk."""
        if os.path.exists(self.index_file) and self.chunks:
            try:
                with open(self.index_file, 'rb') as f:
                    data = pickle.load(f)
                    self.vectorizer = data.get('vectorizer')
                    self.tfidf_matrix = data.get('tfidf_matrix')
            except:
                self._rebuild_index()

    def _save_index(self):
        """Save TF-IDF index to disk."""
        if self.vectorizer and self.tfidf_matrix is not None:
            with open(self.index_file, 'wb') as f:
                pickle.dump({
                    'vectorizer': self.vectorizer,
                    'tfidf_matrix': self.tfidf_matrix
                }, f)

    def _rebuild_index(self):
        """Rebuild the TF-IDF index from chunks."""
        if not SKLEARN_AVAILABLE or not self.chunks:
            return

        texts = [chunk['text'] for chunk in self.chunks]

        # Create TF-IDF vectorizer with pentesting-aware settings
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),  # Unigrams and bigrams
            stop_words='english',
            min_df=1,
            max_df=0.95
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        self._save_index()

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file."""
        text = ""

        # Try pdfplumber first (better quality)
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
                if text.strip():
                    return text
            except Exception as e:
                pass

        # Fall back to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
            except Exception as e:
                pass

        return text

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: The text to chunk
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        # Clean the text
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= chunk_size:
            return [text] if text else []

        chunks = []
        start = 0

        while start < len(text):
            # Find end of chunk
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                for punct in ['. ', '.\n', '? ', '!\n', '\n\n']:
                    last_punct = text.rfind(punct, start + chunk_size // 2, end + 100)
                    if last_punct != -1:
                        end = last_punct + len(punct)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start with overlap
            start = end - overlap
            if start <= 0 or start >= len(text):
                break

        return chunks

    def add_document(self, file_path: str, title: str = None,
                    progress_callback=None) -> Tuple[bool, str]:
        """
        Add a document to the knowledge base.

        Args:
            file_path: Path to the document (PDF or text file)
            title: Optional title for the document
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (success, message)
        """
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        # Determine file type and extract text
        ext = os.path.splitext(file_path)[1].lower()

        if progress_callback:
            progress_callback("Extracting text from document...")

        if ext == '.pdf':
            if not (PYPDF2_AVAILABLE or PDFPLUMBER_AVAILABLE):
                return False, "PDF support requires PyPDF2 or pdfplumber. Install with: pip install PyPDF2 pdfplumber"
            text = self._extract_text_from_pdf(file_path)
        elif ext in ['.txt', '.md', '.rst']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
        else:
            return False, f"Unsupported file type: {ext}"

        if not text.strip():
            return False, "No text could be extracted from the document"

        # Generate document ID
        doc_id = hashlib.md5(f"{file_path}:{os.path.getmtime(file_path)}".encode()).hexdigest()[:12]

        # Check if document already exists
        existing_ids = [d['id'] for d in self.metadata['documents']]
        if doc_id in existing_ids:
            return False, "Document already indexed"

        if progress_callback:
            progress_callback("Chunking text...")

        # Chunk the text
        text_chunks = self._chunk_text(text)

        if not text_chunks:
            return False, "No usable text chunks created"

        if progress_callback:
            progress_callback(f"Creating {len(text_chunks)} chunks...")

        # Add chunks to storage
        doc_title = title or os.path.basename(file_path)
        start_idx = len(self.chunks)

        for i, chunk_text in enumerate(text_chunks):
            self.chunks.append({
                'text': chunk_text,
                'doc_id': doc_id,
                'doc_title': doc_title,
                'chunk_idx': i,
                'total_chunks': len(text_chunks)
            })

        # Update metadata
        self.metadata['documents'].append({
            'id': doc_id,
            'title': doc_title,
            'path': file_path,
            'chunks': len(text_chunks),
            'start_idx': start_idx,
            'added': datetime.now().isoformat()
        })
        self.metadata['total_chunks'] = len(self.chunks)

        # Save chunks
        self._save_chunks()
        self._save_metadata()

        if progress_callback:
            progress_callback("Building search index...")

        # Rebuild index
        if SKLEARN_AVAILABLE:
            self._rebuild_index()

        return True, f"Added '{doc_title}' with {len(text_chunks)} chunks"

    def remove_document(self, doc_id: str) -> Tuple[bool, str]:
        """Remove a document from the knowledge base."""
        # Find document
        doc = None
        for d in self.metadata['documents']:
            if d['id'] == doc_id:
                doc = d
                break

        if not doc:
            return False, "Document not found"

        # Remove chunks for this document
        self.chunks = [c for c in self.chunks if c['doc_id'] != doc_id]

        # Update metadata
        self.metadata['documents'] = [d for d in self.metadata['documents'] if d['id'] != doc_id]
        self.metadata['total_chunks'] = len(self.chunks)

        # Save and rebuild
        self._save_chunks()
        self._save_metadata()

        if self.chunks:
            self._rebuild_index()
        else:
            self.vectorizer = None
            self.tfidf_matrix = None
            if os.path.exists(self.index_file):
                os.remove(self.index_file)

        return True, f"Removed '{doc['title']}'"

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search the knowledge base for relevant chunks.

        Args:
            query: The search query
            top_k: Number of results to return

        Returns:
            List of relevant chunks with scores
        """
        if not SKLEARN_AVAILABLE:
            return []

        if not self.vectorizer or self.tfidf_matrix is None or not self.chunks:
            return []

        # Transform query
        query_vec = self.vectorizer.transform([query])

        # Calculate similarities
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]

        # Filter out low-relevance results
        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score > 0.05:  # Minimum relevance threshold
                chunk = self.chunks[idx].copy()
                chunk['score'] = float(score)
                results.append(chunk)

        return results

    def get_context_for_query(self, query: str, max_tokens: int = 2000) -> str:
        """
        Get relevant context to inject into the model prompt.

        Args:
            query: The user's query
            max_tokens: Approximate max tokens for context

        Returns:
            Formatted context string
        """
        results = self.search(query, top_k=5)

        if not results:
            return ""

        context_parts = ["=== RELEVANT KNOWLEDGE BASE CONTENT ===\n"]
        total_chars = 0
        char_limit = max_tokens * 4  # Rough char-to-token ratio

        for i, result in enumerate(results):
            chunk_text = result['text']
            doc_title = result['doc_title']
            score = result['score']

            # Check if we have room
            chunk_header = f"\n[From: {doc_title}] (relevance: {score:.2f})\n"
            if total_chars + len(chunk_header) + len(chunk_text) > char_limit:
                break

            context_parts.append(chunk_header)
            context_parts.append(chunk_text)
            total_chars += len(chunk_header) + len(chunk_text)

        context_parts.append("\n=== END KNOWLEDGE BASE CONTENT ===\n")
        context_parts.append("Use the above information to help answer the user's question.\n")

        return '\n'.join(context_parts)

    def get_stats(self) -> Dict:
        """Get statistics about the knowledge base."""
        return {
            'num_documents': len(self.metadata.get('documents', [])),
            'total_chunks': self.metadata.get('total_chunks', 0),
            'last_updated': self.metadata.get('last_updated'),
            'documents': self.metadata.get('documents', []),
            'sklearn_available': SKLEARN_AVAILABLE,
            'pdf_available': PYPDF2_AVAILABLE or PDFPLUMBER_AVAILABLE
        }

    def clear(self) -> Tuple[bool, str]:
        """Clear all documents from the knowledge base."""
        self.chunks = []
        self.metadata = {
            "documents": [],
            "total_chunks": 0,
            "last_updated": None,
            "version": "1.0"
        }
        self.vectorizer = None
        self.tfidf_matrix = None

        # Remove files
        for f in [self.index_file, self.chunks_file]:
            if os.path.exists(f):
                os.remove(f)

        self._save_metadata()

        return True, "Knowledge base cleared"


# Convenience functions for the GUI
def check_dependencies() -> Dict[str, bool]:
    """Check which optional dependencies are available."""
    return {
        'sklearn': SKLEARN_AVAILABLE,
        'pypdf2': PYPDF2_AVAILABLE,
        'pdfplumber': PDFPLUMBER_AVAILABLE,
        'pdf_support': PYPDF2_AVAILABLE or PDFPLUMBER_AVAILABLE
    }


def install_command() -> str:
    """Return pip install command for missing dependencies."""
    deps = []
    if not SKLEARN_AVAILABLE:
        deps.append('scikit-learn')
    if not PYPDF2_AVAILABLE and not PDFPLUMBER_AVAILABLE:
        deps.append('PyPDF2')
        deps.append('pdfplumber')

    if deps:
        return f"pip install {' '.join(deps)}"
    return ""
