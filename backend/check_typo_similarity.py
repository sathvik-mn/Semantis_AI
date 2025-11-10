"""
Check the actual similarity between "what is comptr" and "what iz comptr"
"""
import os
from dotenv import load_dotenv
import openai
import numpy as np

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_embedding(text: str) -> np.ndarray:
    """Return L2-normalized embedding vector."""
    resp = openai.embeddings.create(model="text-embedding-3-large", input=text)
    v = np.array(resp.data[0].embedding, dtype="float32")
    v /= (np.linalg.norm(v) + 1e-12)
    return v

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return float(np.dot(v1, v2))

# Test queries
query1 = "what is comptr"
query2 = "what iz comptr"

print("=" * 60)
print("Checking Similarity Between Typo Queries")
print("=" * 60)
print(f"\nQuery 1: '{query1}'")
print(f"Query 2: '{query2}'")

# Get embeddings
print("\nGetting embeddings...")
emb1 = get_embedding(query1)
emb2 = get_embedding(query2)

# Calculate similarity
similarity = cosine_similarity(emb1, emb2)

print(f"\nSimilarity: {similarity:.4f}")
print(f"Threshold (current): 0.72")
print(f"Threshold (typo tolerance): 0.65")

if similarity >= 0.72:
    print(f"\n[OK] Similarity {similarity:.4f} >= 0.72 (will match)")
elif similarity >= 0.65:
    print(f"\n[OK] Similarity {similarity:.4f} >= 0.65 (will match with typo tolerance)")
else:
    print(f"\n[ISSUE] Similarity {similarity:.4f} < 0.65 (will NOT match)")
    print(f"       Need to lower threshold further for typo tolerance")

# Also test with "computer" (correct spelling)
print("\n" + "=" * 60)
print("Comparing with correct spelling:")
query3 = "what is computer"
print(f"Query 3: '{query3}'")
emb3 = get_embedding(query3)
sim1_3 = cosine_similarity(emb1, emb3)
sim2_3 = cosine_similarity(emb2, emb3)

print(f"\nSimilarity between '{query1}' and '{query3}': {sim1_3:.4f}")
print(f"Similarity between '{query2}' and '{query3}': {sim2_3:.4f}")
print(f"Similarity between '{query1}' and '{query2}': {similarity:.4f}")

