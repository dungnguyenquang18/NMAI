import re
import google.generativeai as genai
import time
import os
from dotenv import load_dotenv
load_dotenv()


class Chatbot():
    def __init__(self):
        # Thay thế bằng API Key của bạn
        self.API_KEY = os.getenv('API_KEY')
        # Cấu hình API Key
        genai.configure(api_key=self.API_KEY)
        # Khởi tạo mô hình Gemini Pro
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        

    def answer(self, query):
        result = self.model.generate_content(query).text
        return result
    
