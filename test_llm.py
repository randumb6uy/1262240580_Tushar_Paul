import os
from dotenv import load_dotenv
from llama_index.llms.openrouter import OpenRouter

# 1. Load environment variables from .env
load_dotenv()

# 2. Set up the OpenRouter LLM
llm = OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="nvidia/nemotron-3.5-lightning:free",
    max_tokens=1024,  # prevents empty responses from reasoning models
)

# 3. Send a simple test prompt
response = llm.complete("Say hello in one sentence.")

# 4. Print the result
print("Response:", response)