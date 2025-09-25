from google import genai
from dotenv import load_dotenv
import os

load_dotenv(override=True)

API_KEY=os.environ.get("GEMINI_API_KEY")

print(API_KEY)

client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="How does AI work?"
)
print(response.text)