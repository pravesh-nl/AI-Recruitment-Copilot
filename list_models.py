from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv(override=True)
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

for model in client.models.list():
    print(model.name)
    