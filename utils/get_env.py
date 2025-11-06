from dotenv import load_dotenv
import os

load_dotenv()
def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"{var_name} not found in environment (.env)")
    return value