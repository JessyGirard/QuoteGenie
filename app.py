from dotenv import load_dotenv
import os
from openai import OpenAI

# Load .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize client
client = OpenAI(api_key=api_key)

try:
    # Make a safe GPT request with token cap
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=200,  # response limited to ~200 tokens
        messages=[
            {
                "role": "user",
                "content": "Hello from VS Code! Write me a short motivational message.",
            }
        ],
    )

    print("GPT says:", response.choices[0].message.content)

except Exception as e:
    print("⚠️ Error:", str(e))
