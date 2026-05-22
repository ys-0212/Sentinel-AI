# NLP Similarity Module for Complaint Matching
# Uses sentence-transformers for embedding generation and cosine similarity

import numpy as np
from typing import List, Optional, Tuple, Dict
import pickle
import os
from collections import OrderedDict
from functools import lru_cache

# Try importing sentence-transformers, provide fallback
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMER_AVAILABLE = False
    print("Warning: sentence-transformers not installed. Run: pip install sentence-transformers")

# Model configuration
MODEL_NAME = "all-MiniLM-L6-v2"  # Lightweight, fast, good for semantic similarity
EMBEDDING_DIM = 384  # Dimension of vectors from this model
DEFAULT_SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.6"))
MAX_EMBEDDING_SIZE_MB = 10  # Maximum embedding size in MB

# Global model instance (loaded on first use)
_model = None

# LRU Cache for embeddings (max 100 items)
class EmbeddingCache:
    def __init__(self, max_size=100):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key):
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                self.cache.popitem(last=False)
            self.cache[key] = value
    
    def clear(self):
        self.cache.clear()

_embedding_cache = EmbeddingCache()


def get_model():
    """Lazily load the sentence transformer model."""
    global _model
    if _model is None:
        if not SENTENCE_TRANSFORMER_AVAILABLE:
            raise ImportError("sentence-transformers is not installed")
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def generate_embedding(text: str) -> np.ndarray:
    """
    Generate a 384-dimensional embedding vector for the given text.
    
    Args:
        text: Input text (complaint text or summary)
        
    Returns:
        numpy array of shape (384,)
    """
    if not SENTENCE_TRANSFORMER_AVAILABLE:
        # Return random vector as fallback for testing
        return np.random.randn(EMBEDDING_DIM).astype(np.float32)
    
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.astype(np.float32)


def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Since embeddings are normalized, this is just the dot product.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Similarity score between -1 and 1 (higher = more similar)
    """
    return float(np.dot(embedding1, embedding2))


def embedding_to_bytes(embedding: np.ndarray) -> bytes:
    """
    Serialize embedding to bytes for database storage.
    Validates size before serialization.
    """
    serialized = pickle.dumps(embedding)
    size_mb = len(serialized) / (1024 * 1024)
    if size_mb > MAX_EMBEDDING_SIZE_MB:
        raise ValueError(f"Embedding size ({size_mb:.2f}MB) exceeds maximum allowed ({MAX_EMBEDDING_SIZE_MB}MB)")
    return serialized


def bytes_to_embedding(data: bytes) -> np.ndarray:
    """
    Deserialize embedding from database bytes.
    Handles corrupted data gracefully.
    """
    try:
        embedding = pickle.loads(data)
        # Validate embedding shape and type
        if not isinstance(embedding, np.ndarray):
            raise ValueError("Deserialized data is not a numpy array")
        if embedding.shape != (EMBEDDING_DIM,):
            raise ValueError(f"Invalid embedding shape: {embedding.shape}, expected ({EMBEDDING_DIM},)")
        return embedding
    except (pickle.UnpicklingError, ValueError, AttributeError) as e:
        raise ValueError(f"Corrupted embedding data: {str(e)}")


def find_similar_texts(
    query_embedding: np.ndarray,
    embeddings: List[Tuple[str, np.ndarray]],  # List of (id, embedding)
    threshold: float = None,
    top_k: int = 5
) -> List[Tuple[str, float]]:
    """
    Find texts most similar to the query.
    
    Args:
        query_embedding: The embedding to find similar texts for
        embeddings: List of (id, embedding) tuples to search through
        threshold: Minimum similarity score (0-1), defaults to DEFAULT_SIMILARITY_THRESHOLD
        top_k: Maximum number of results
        
    Returns:
        List of (id, similarity_score) tuples, sorted by similarity descending
    """
    if threshold is None:
        threshold = DEFAULT_SIMILARITY_THRESHOLD
    
    results = []
    
    for id_, emb in embeddings:
        try:
            similarity = calculate_similarity(query_embedding, emb)
            if similarity >= threshold:
                results.append((id_, similarity))
        except Exception as e:
            print(f"Warning: Failed to calculate similarity for {id_}: {e}")
            continue
    
    # Sort by similarity (descending)
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:top_k]


def batch_generate_embeddings(texts: List[str]) -> List[np.ndarray]:
    """
    Generate embeddings for multiple texts in batch (more efficient).
    
    Args:
        texts: List of text strings
        
    Returns:
        List of embedding arrays
    """
    if not SENTENCE_TRANSFORMER_AVAILABLE:
        # Return random vectors as fallback
        return [np.random.randn(EMBEDDING_DIM).astype(np.float32) for _ in texts]
    
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, batch_size=32)
    return [emb.astype(np.float32) for emb in embeddings]


# --- Database Integration Functions ---

def get_complaint_embedding_from_db(complaint_id: str, db_connection) -> Optional[np.ndarray]:
    """
    Retrieve a complaint's embedding from the database with caching.
    
    Args:
        complaint_id: The complaint ID
        db_connection: SQLite connection
        
    Returns:
        Embedding array or None if not found
    """
    # Check cache first
    cached = _embedding_cache.get(complaint_id)
    if cached is not None:
        return cached
    
    cursor = db_connection.cursor()
    cursor.execute("SELECT embedding FROM complaints WHERE complaint_id = ?", (complaint_id,))
    row = cursor.fetchone()
    
    if row and row[0]:
        try:
            embedding = bytes_to_embedding(row[0])
            # Cache the embedding
            _embedding_cache.set(complaint_id, embedding)
            return embedding
        except ValueError as e:
            print(f"Warning: Corrupted embedding for complaint {complaint_id}: {e}")
            return None
        except Exception as e:
            print(f"Error loading embedding for complaint {complaint_id}: {e}")
            return None
    return None


def get_all_complaint_embeddings(db_connection, exclude_id: str = None) -> List[Tuple[str, np.ndarray]]:
    """
    Get all complaint embeddings from database.
    
    Args:
        db_connection: SQLite connection
        exclude_id: Optional complaint ID to exclude (usually the query complaint)
        
    Returns:
        List of (complaint_id, embedding) tuples
    """
    cursor = db_connection.cursor()
    
    if exclude_id:
        cursor.execute("SELECT complaint_id, embedding FROM complaints WHERE embedding IS NOT NULL AND complaint_id != ?", (exclude_id,))
    else:
        cursor.execute("SELECT complaint_id, embedding FROM complaints WHERE embedding IS NOT NULL")
    
    results = []
    for row in cursor.fetchall():
        try:
            embedding = bytes_to_embedding(row[1])
            results.append((row[0], embedding))
        except Exception:
            continue
    
    return results


def find_similar_complaints(
    complaint_id: str,
    db_connection,
    threshold: float = None,
    limit: int = 5
) -> List[dict]:
    """
    Find complaints similar to the given complaint.
    
    Args:
        complaint_id: The complaint to find similar ones for
        db_connection: SQLite connection  
        threshold: Minimum similarity score (0-1), defaults to DEFAULT_SIMILARITY_THRESHOLD
        limit: Maximum number of results
        
    Returns:
        List of dicts with complaint details and similarity scores
    """
    if threshold is None:
        threshold = DEFAULT_SIMILARITY_THRESHOLD
    
    # Get the query complaint's embedding
    query_embedding = get_complaint_embedding_from_db(complaint_id, db_connection)
    
    if query_embedding is None:
        print(f"Warning: No embedding found for complaint {complaint_id}")
        return []
    
    # Get all other embeddings
    all_embeddings = get_all_complaint_embeddings(db_connection, exclude_id=complaint_id)
    
    if not all_embeddings:
        return []
    
    # Find similar
    similar_ids = find_similar_texts(query_embedding, all_embeddings, threshold, limit)
    
    # Fetch full complaint details for results
    results = []
    cursor = db_connection.cursor()
    
    for similar_id, similarity_score in similar_ids:
        cursor.execute(
            "SELECT complaint_id, crime_type, narrative_summary, status FROM complaints WHERE complaint_id = ?",
            (similar_id,)
        )
        row = cursor.fetchone()
        if row:
            results.append({
                'complaint_id': row[0],
                'crime_type': row[1],
                'narrative_summary': row[2],
                'status': row[3],
                'similarity_score': round(similarity_score, 3)
            })
    
    return results


def save_complaint_embedding(complaint_id: str, embedding: np.ndarray, db_connection):
    """
    Save an embedding to the database for a complaint.
    
    Args:
        complaint_id: The complaint ID
        embedding: The embedding array
        db_connection: SQLite connection
    """
    cursor = db_connection.cursor()
    embedding_bytes = embedding_to_bytes(embedding)
    
    cursor.execute(
        "UPDATE complaints SET embedding = ? WHERE complaint_id = ?",
        (embedding_bytes, complaint_id)
    )
    db_connection.commit()


# --- Batch Processing ---

def process_all_complaints(db_connection, batch_size: int = 50):
    """
    Generate embeddings for all complaints that don't have one yet.
    Uses batch processing for efficiency.
    
    Args:
        db_connection: SQLite connection
        batch_size: Number of complaints to process in each batch
        
    Returns:
        Number of complaints processed
    """
    cursor = db_connection.cursor()
    
    # Get complaints without embeddings
    cursor.execute("""
        SELECT complaint_id, complaint_text, narrative_summary 
        FROM complaints 
        WHERE embedding IS NULL
    """)
    
    rows = cursor.fetchall()
    count = 0
    
    # Process in batches for efficiency
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        
        # Prepare texts for batch processing
        batch_data = []
        for complaint_id, complaint_text, narrative_summary in batch:
            text_to_embed = narrative_summary if narrative_summary else complaint_text
            if text_to_embed:
                batch_data.append((complaint_id, text_to_embed))
        
        if not batch_data:
            continue
        
        try:
            # Generate embeddings in batch
            texts = [text for _, text in batch_data]
            embeddings = batch_generate_embeddings(texts)
            
            # Save all embeddings
            for (complaint_id, _), embedding in zip(batch_data, embeddings):
                try:
                    save_complaint_embedding(complaint_id, embedding, db_connection)
                    count += 1
                    if count % 10 == 0:
                        print(f"Processed {count} complaints...")
                except Exception as e:
                    print(f"Error saving embedding for complaint {complaint_id}: {e}")
        
        except Exception as e:
            print(f"Error processing batch: {e}")
            # Fall back to individual processing for this batch
            for complaint_id, text in batch_data:
                try:
                    embedding = generate_embedding(text)
                    save_complaint_embedding(complaint_id, embedding, db_connection)
                    count += 1
                except Exception as e:
                    print(f"Error processing complaint {complaint_id}: {e}")
    
    print(f"✓ Generated embeddings for {count} complaints")
    return count


def clear_embedding_cache():
    """Clear the embedding cache."""
    _embedding_cache.clear()
    print("✓ Embedding cache cleared")


if __name__ == "__main__":
    # Test the module
    print(f"sentence-transformers available: {SENTENCE_TRANSFORMER_AVAILABLE}")
    
    if SENTENCE_TRANSFORMER_AVAILABLE:
        # Test embedding generation
        test_text = "I was scammed through a fake customer care call and lost Rs. 50,000"
        embedding = generate_embedding(test_text)
        print(f"Generated embedding shape: {embedding.shape}")
        print(f"Embedding dtype: {embedding.dtype}")
        
        # Test similarity
        text2 = "Fraudster pretending to be bank customer care stole my money"
        text3 = "My laptop was stolen from my office"
        
        emb1 = generate_embedding(test_text)
        emb2 = generate_embedding(text2)
        emb3 = generate_embedding(text3)
        
        print(f"\nSimilarity (fraud-fraud): {calculate_similarity(emb1, emb2):.3f}")
        print(f"Similarity (fraud-theft): {calculate_similarity(emb1, emb3):.3f}")
    else:
        print("Install sentence-transformers to test: pip install sentence-transformers")
