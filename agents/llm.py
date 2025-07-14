"""
Shared LLM models and utilities for legal agents.
"""
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()

model = ChatGoogleGenerativeAI(
    model=os.getenv('GEMINI_MODEL'),
    temperature=os.getenv('DEFAULT_TEMPERATURE', 0.5),
    max_tokens=os.getenv('MAX_TOKENS', None),
)

embeddings = GoogleGenerativeAIEmbeddings(
    model=os.getenv('GEMINI_EMBEDDINGS'),
)
