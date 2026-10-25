import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")

req = urllib.request.Request(
    "https://generativelanguage.googleapis.com/v1beta/models?pageSize=200",
    headers={"x-goog-api-key": key},
)

with urllib.request.urlopen(req) as resp:
    data = json.load(resp)

for m in data.get("models", []):
    methods = m.get("supportedGenerationMethods", [])
    if "generateContent" in methods or "embedContent" in methods:
        print(m["name"], methods)