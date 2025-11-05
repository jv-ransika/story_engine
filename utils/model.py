import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv() 
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY not found in environment (.env)")

lite_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", api_key=api_key)
advanced_llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", api_key=api_key)