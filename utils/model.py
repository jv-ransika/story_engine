from langchain_google_genai import ChatGoogleGenerativeAI
from utils.get_env import get_env_variable


api_key = get_env_variable("GOOGLE_API_KEY")

lite_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", api_key=api_key)
advanced_llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", api_key=api_key)