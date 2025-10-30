import requests
import json
import os

OPENROUTER_API_KEY="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"  # store in environment variable for safety

def run_agent(prompt, context=None, model="openai/gpt-4o"):
    if not OPENROUTER_API_KEY:
        raise ValueError("Missing OpenRouter API key. Set OPENROUTER_API_KEY in your environment.")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",  # optional, for site ranking
        "X-Title": "My AI Agent",  # optional
    }

    messages = [{"role": "user", "content": prompt}]
    if context:
        messages.insert(0, {"role": "system", "content": context})

    data = {
        "model": model,
        "messages": messages
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code != 200:
        return f"Error: {response.status_code}, {response.text}"

    result = response.json()
    return result["choices"][0]["message"]["content"]
