import torch
import torch.nn as nn
import numpy as np
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import tiktoken
import pandas as pd
import random
from itertools import combinations
import math

# Kiểm tra GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
# Positional Encoding
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1), :]
        return x

# Transformer Encoder Layer
class TransformerEncoderLayer(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super(TransformerEncoderLayer, self).__init__()
        self.num_heads = num_heads
        self.d_model = d_model
        self.depth = d_model // num_heads
        self.wq = nn.Linear(d_model, d_model)
        self.wk = nn.Linear(d_model, d_model)
        self.wv = nn.Linear(d_model, d_model)
        self.dense = nn.Linear(d_model, d_model)
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Linear(d_ff, d_model)
        )
        self.layernorm1 = nn.LayerNorm(d_model)
        self.layernorm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def split_heads(self, x, batch_size):
        x = x.view(batch_size, -1, self.num_heads, self.depth)
        return x.transpose(1, 2)

    def scaled_dot_product_attention(self, q, k, v, mask=None):
        matmul_qk = torch.matmul(q, k.transpose(-2, -1))
        dk = torch.tensor(k.size(-1), dtype=torch.float32)
        scaled_attention_logits = matmul_qk / torch.sqrt(dk)
        if mask is not None:
            scaled_attention_logits = scaled_attention_logits.masked_fill(mask == 0, -1e9)
        attention_weights = torch.nn.functional.softmax(scaled_attention_logits, dim=-1)
        output = torch.matmul(attention_weights, v)
        return output, attention_weights

    def forward(self, x, mask=None):
        batch_size = x.size(0)
        q = self.split_heads(self.wq(x), batch_size)
        k = self.split_heads(self.wk(x), batch_size)
        v = self.split_heads(self.wv(x), batch_size)
        scaled_attention, _ = self.scaled_dot_product_attention(q, k, v, mask)
        scaled_attention = scaled_attention.transpose(1, 2).contiguous()
        concat_attention = scaled_attention.view(batch_size, -1, self.d_model)
        attn_output = self.dense(concat_attention)
        x = self.layernorm1(x + self.dropout(attn_output))
        ff_output = self.feed_forward(x)
        x = self.layernorm2(x + self.dropout(ff_output))
        return x

# Transformer Model (chỉ encoder)
class TransformerModel(nn.Module):
    def __init__(self, vocab_size, embed_size, d_model, num_heads, d_ff, num_layers=4, dropout=0.1):
        super(TransformerModel, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_size)
        self.positional_encoding = PositionalEncoding(d_model)
        self.encoder_layers = nn.ModuleList([
            TransformerEncoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        x = self.embedding(x)
        x = self.positional_encoding(x)
        for layer in self.encoder_layers:
            x = layer(x, mask)
        return x  # (batch_size, seq_len, d_model)


# Hàm inference để tạo embedding
def get_embedding(text, tokenizer, model, max_length=500, device='cuda'):
    # Chuyển model sang chế độ đánh giá
    model.eval()
    
    # Tiền xử lý văn bản
    text = str(text).lower()  # Chuyển thành lowercase
    encoding = tokenizer.encode(text)
    
    # Chia thành các chunk nếu dài hơn max_length
    chunks = []
    for start in range(0, len(encoding), max_length):
        end = min(start + max_length, len(encoding))
        chunk = encoding[start:end]
        chunks.append(chunk)
    # print(len(chunks))
    
    # Tạo embedding cho từng chunk
    embeddings = []
    with torch.no_grad():
        for chunk in chunks:
            input_ids = torch.tensor([chunk], dtype=torch.long).to(device)  # Thêm batch dimension
            output = model(input_ids)  # (1, seq_len, d_model)
            # Mean pooling để lấy embedding cố định cho chunk
            embedding = output.mean(dim=1).squeeze().cpu().numpy()  # (d_model,)
            embeddings.append(embedding)
    
    # Nếu có nhiều chunk, lấy trung bình các embedding
    if len(embeddings) > 1:
        embedding = np.mean(embeddings, axis=0)
    else:
        embedding = embeddings[0]
    
    return embedding


