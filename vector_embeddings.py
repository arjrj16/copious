import torch
import numpy as np
from transformers import AutoTokenizer

def chunk_text(text, max_tokens, tokenizer):
    tokens = tokenizer.encode(text, add_special_tokens=False)
    all_chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = tokens[i:i+max_tokens]
        all_chunks.append(chunk)
    
    all_chunks = [tokenizer.decode(chunk, skip_special_tokens=True) for chunk in all_chunks]
    return all_chunks

def get_embeddings(text, model, tokenizer, max_length):
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=max_length)
    with torch.no_grad():
        outputs = model(**inputs)
    embedding = mean_pooling(model_output, encoded_input['attention_mask'])
    return embedding.numpy()  

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state  # shape: (batch_size, sequence_length, hidden_size)
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, dim=1)
    sum_mask = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
    return sum_embeddings / sum_mask


def document_embeddings(text, tokenizer, model, max_length):
    chunks = chunk_text(text, max_length, tokenizer)
    embeddings = []
    for chunk in chunks:
        embedding = get_embeddings(chunk, model, tokenizer, max_length)
        embeddings.append(embedding)
    aggregrated_embeddings = np.mean(np.vstack(embeddings), axis = 0)
    return aggregrated_embeddings

def final_embeddings(docs):
    model_name="sentence-transformers/multilingual-e5-large"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model=AutoModel.from_pretrained(model_name)
    embeddings = {}
    documents = docs
    for i, doc in enumerate(documents):
        aggregated_embeddings = document_embeddings(doc, tokenizer, model, 96)
        embeddings[i] = aggregated_embeddings
    return embeddings