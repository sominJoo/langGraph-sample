from decouple import config
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama


# 추후 settings.OPENAI_API_KEY로 호출
OPENAI_API_KEY = config("OPENAI_API_KEY")
TAVILY_API_KEY = config("TAVILY_API_KEY")

# LLM model setting
LLM = {
    "openAI": ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo"),
    "llama3": Ollama(model="llama3")
}.get(config("LLM"), None)
