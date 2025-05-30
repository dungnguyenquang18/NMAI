import torch
import torch.nn as nn
import tiktoken
from embeding_model.model import get_embedding
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from langchain.schema import Document
import torch
import numpy as np
from langchain_community.vectorstores import FAISS

class Retriever:
    def __init__(self):
        pass

    def retrieve(self, query, tokenizer, model, k, device='cpu'):

        faiss_index = FAISS.load_local(
            folder_path="D:/3Y2S/AI/btl/nmai/vector_db",
            embeddings=None,
            allow_dangerous_deserialization=True  # Bắt buộc phải thêm tham số này
        )

        #
        # Lấy embedding query
        query_embedding = get_embedding(query, tokenizer, model, max_length=500, device=device)

        # Tìm kiếm top k kết quả gần nhất trong FAISS
        k = 5
        results = faiss_index.similarity_search_by_vector(query_embedding, k=k)
        information = ""
        for doc in results:
            information += doc.page_content + "\n"
        return results
