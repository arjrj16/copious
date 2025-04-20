from pinecone import Pinecone, ServerlessSpec
from transformers import AutoTokenizer
from vector_embeddings import final_embeddings
import time
from email_preprocessing import fetch_first_n_emails, get_gmail_service
pc = Pinecone(api_key="pcsk_3DGuoh_3cqeJ3msXduq2r4PrHCCh9EWceg4CGE2WksZEuh2vNAwAw9yLxZeFz24LaDrhjv")
index = "semanticsearch7"
pc.create_index(
    name=index,
    dimension=1024, # Replace with your model dimensions
    metric="cosine", # Replace with your model metric
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    ) 
)
service=get_gmail_service()
data=fetch_first_n_emails(service)
#inputs = [i["body"] for i in data]
#embeddings = final_embeddings(inputs)
embeddings = openai.embeddings.create(
    model="text-embedding-3-small",
    inputs=[i["body"] for i in data],
    parameters={"input_type": "passage", "truncate": "END"}
)

while not pc.describe_index(index).status['ready']:
    time.sleep(1)

index = pc.Index(index)

vectors = []
for d, e in zip(data, embeddings):
    vectors.append({
        "id": d['id'],
        "values": e['values'],
        "metadata": {'text': d['text']}
    })

index.upsert(
    vectors=vectors,
    namespace="ns1"
)

print(index.describe_index_stats())

query = "Uber"
query_embedding = pc.inference.embed(
    model = "text-embedding-3-small",
    inputs = [query],
    parameters = {
        "input_type": "query"
        }
)

results = index.query(
    namespace = "ns1",
    vector = query_embedding[0].values,
    top_k=3,
    include_values=False,
    include_metadata = True,
)

print(results)