import os, requests
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("GEMINI_API_KEY_1")
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + key
data = {"contents": [{"parts": [{"text": "Say hello"}]}]}
r = requests.post(url, headers={"Content-Type": "application/json"}, json=data)
print(r.status_code, r.text)
