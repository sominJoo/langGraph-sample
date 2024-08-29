import os

from decouple import config
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama

OPENAI_API_KEY = config("OPENAI_API_KEY")
TAVILY_API_KEY = config("TAVILY_API_KEY")

# LLM model setting
LLM = {
    "openAI": ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o"),
    "llama3": Ollama(model="llama3")
}.get(config("LLM"), None)

os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

# Postgresql 연결정보
POSTGRES_USERNAME = config("POSTGRES_USERNAME")
POSTGRES_PASSWORD = config("POSTGRES_PASSWORD")
POSTGRES_HOST = config("POSTGRES_HOST")
POSTGRES_PORT = config("POSTGRES_PORT")
POSTGRES_DATABASE = config("POSTGRES_DATABASE")
POSTGRES_SCHEMA = config("POSTGRES_SCHEMA")
