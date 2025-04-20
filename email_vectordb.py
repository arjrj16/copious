import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from email_preprocessing import get_gmail_service, fetch_first_n_emails
import hashlib
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

class EmailVectorDB:
    def __init__(self, index_name="email-index"):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        dimension = self.model.get_sentence_embedding_dimension()
        try:
            if index_name in pc.list_indexes().names():
                pc.delete_index(index_name)
            
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )
            
            self.index = pc.Index(index_name)
            print(f"Created/connected to index '{index_name}' with dimension {dimension}")
            
        except Exception as e:
            print(f"Error creating/connecting to index: {e}")
            raise
    
    def create_email_embedding(self, email: Dict[str, Any]) -> List[float]:
        return self.model.encode(email['body']).tolist()
    
    def generate_email_id(self, email: Dict[str, Any]) -> str:
        content = f"{email['subject']}{email['sender']}{email['body'][:100]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_emails(self, emails: List[Dict[str, Any]]) -> None:
        vectors = []
        for email in emails:
            email_id = self.generate_email_id(email)
            embedding = self.create_email_embedding(email)
            
            vectors.append({
                'id': email_id,
                'values': embedding,
                'metadata': {
                    'subject': email['subject'],
                    'sender': email['sender'],
                    'body': email['body']
                }
            })
        
        # Batch upsert to Pinecone
        self.index.upsert(vectors=vectors)
    
    def search_emails(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        query_embedding = self.model.enexcode(query).tolist()
        
        results = self.index.query(
            vector=query_embedding,
            top_k=n_results,
            include_metadata=True
        )
        
        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append({
                'id': match.id,
                'subject': match.metadata['subject'],
                'sender': match.metadata['sender'],
                'body': match.metadata['body'],
                'score': match.score
            })
        
        return formatted_results

def main():
    # Initialize the vector database
    email_db = EmailVectorDB()
    
    # Fetch emails using the existing preprocessing code
    service = get_gmail_service()
    emails = fetch_first_n_emails(service, n=100)  # Adjust n as needed
    
    # Add emails to the vector database
    print(f"Adding {len(emails)} emails to the vector database...")
    email_db.add_emails(emails)
    print("Emails added successfully!")
    
    # Example search
    while True:
        query = input("\nEnter a search query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
            
        results = email_db.search_emails(query)
        print(f"\nTop {len(results)} relevant emails:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Subject: {result['subject']}")
            print(f"   From: {result['sender']}")
            print(f"   Preview: {result['body'][:200]}...")
            print(f"   Relevance Score: {result['score']:.2f}")

if __name__ == "__main__":
    main() 