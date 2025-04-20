import openai
import pinecone
from pinecone import Pinecone, ServerlessSpec
from transformers import AutoTokenizer
from vector_embeddings import final_embeddings
import time
from email_preprocessing import fetch_first_n_emails, get_gmail_service

# Initialize OpenAI (set your API key here)
openai.api_key = ""

# Initialize Pinecone (set your API key and environment here)
pinecone.init(api_key="", environment="us-east1-gcp")

# Create Pinecone index
index_name = "index"

if index_name not in pinecone.list_indexes():
    pinecone.create_index(index_name, dimension=1536, metric="cosine")

# Connect to the index
index = pinecone.Index(index_name)

# Dummy data
texts = [
    "This is a test sentence.",
    "Another example text for embeddings.",
    "Machine learning is fascinating.",
    "ChatGPT is a powerful AI model.",
    "Vector databases allow efficient retrieval."
]

# Generate embeddings using OpenAI
embeddings = [openai.Embedding.create(input=text, model="text-embedding-ada-002")["data"][0]["embedding"] for text in texts]

# Prepare and insert vectors into Pinecone
vectors = [(f"id_{i}", embedding, {"text": texts[i]}) for i, embedding in enumerate(embeddings)]
index.upsert(vectors=vectors)

# Function to query Pinecone index
def query_pinecone(query_text, top_k=3):
    query_embedding = openai.Embedding.create(input=query_text, model="text-embedding-ada-002")["data"][0]["embedding"]
    results = index.query(queries=[query_embedding], top_k=top_k, include_metadata=True)
    return results

# Example query
query = "Tell me about AI models."
results = query_pinecone(query)

print("Query Results:")
for match in results['results'][0]['matches']:
    print(f"ID: {match['id']}, Score: {match['score']:.3f}, Text: {match['metadata']['text']}")
