from flask import Flask, request, jsonify
import tiktoken
import torch
from retrive import Retriever
from embeding_model.model import TransformerModel
from main_model import Chatbot

app = Flask(__name__)
# Khởi tạo tokenizer
tokenizer = tiktoken.get_encoding('gpt2')

# Khởi tạo mô hình
vocab_size = tokenizer.n_vocab
embed_size = 512
d_model = 512
num_heads = 8
d_ff = 512
num_layers = 4
dropout = 0.1
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = TransformerModel(vocab_size, embed_size, d_model, num_heads, d_ff, num_layers, dropout)
model.load_state_dict(torch.load('D:/3Y2S/AI/btl/NMAI/best_transformer_encoder_single.pt', map_location=device))
model.to(device)
retrieve = Retriever()
llm = Chatbot()

@app.route('/api/chatbot', methods=['POST'])
def handle_query():
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    information = retrieve.retrieve(query, tokenizer, model, k=5, device=device)
    
    answer = llm.answer(f"hãy viết resume ở ịnh dạng HTML cho tôi từ đoạn thông tin có cấu trúc giống json:\n({query}) \ntừ dữ liệu sau:\n{information}")
    return jsonify(answer)


if __name__ == '__main__':
    app.run(debug=True, port=5000)