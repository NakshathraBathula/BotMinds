import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load the cleaned JSON file
with open("cleaned_data.json", "r", encoding="utf-8") as f:
    cleaned_data = json.load(f)

# Initialize the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Extract text content and URLs for embedding and metadata
texts = [entry["content"] for entry in cleaned_data if entry["content"].strip()]
urls = [entry["url"] for entry in cleaned_data if entry["content"].strip()]

# Generate embeddings in batches to save memory
batch_size = 100
embeddings_list = []
for i in range(0, len(texts), batch_size):
    batch = texts[i:i + batch_size]
    batch_embeddings = model.encode(batch, convert_to_numpy=True)
    embeddings_list.append(batch_embeddings)
embeddings = np.vstack(embeddings_list)

# Create a FAISS index using L2 distance (for small to medium datasets)
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Save FAISS index and metadata
faiss.write_index(index, "data/faiss_index.bin")
with open("data/faiss_metadata.json", "w", encoding="utf-8") as f:
    json.dump({"texts": texts, "urls": urls}, f, indent=4, ensure_ascii=False)

print("FAISS index and metadata saved.")


