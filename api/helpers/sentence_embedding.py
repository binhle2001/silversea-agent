from sentence_transformers import SentenceTransformer
import torch

# Kiểm tra thiết bị có GPU không
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model_embedding = SentenceTransformer('BAAI/bge-m3', device=device)