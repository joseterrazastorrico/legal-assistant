"""
Shared LLM models and utilities for legal agents.
"""
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()

model = AzureChatOpenAI(
    azure_deployment=os.getenv('AZURE_DEPLOYMENT'),
    api_version=os.getenv('API_VERSION'),
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_ENDPOINT'),
    temperature=os.getenv('DEFAULT_TEMPERATURE', 0.1),
    max_tokens=os.getenv('MAX_TOKENS', 4096),
)

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=os.getenv('AZURE_EMBEDDINGS_DEPLOYMENT'),
    api_version=os.getenv('API_VERSION'),
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_ENDPOINT'),
)
