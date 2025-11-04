import os
import json
import requests
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urljoin

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- Detect environment ---
def is_render_env():
    """Return True if running on Render, False if local."""
    return "RENDER" in os.environ or "RENDER_EXTERNAL_URL" in os.environ

IS_RENDER = is_render_env()

# --- Configure CORS dynamically ---
if IS_RENDER:
    print("🌐 Running in Render environment")
    allowed_origins = ["https://joelofthesharingan.github.io"]
else:
    print("💻 Running locally")
    allowed_origins = ["http://localhost:5173"]

CORS(app, resources={r"/*": {"origins": allowed_origins}})

# --- API Keys ---
GEMINI_API_KEY_1 = os.getenv("GEMINI_API_KEY_1")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")

# --- Gemini Models ---
GEMINI_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]


def ask_gemini(prompt, system_prompt=""):
    """Try Gemini models in order with both API keys."""
    combined_prompt = f"{system_prompt}\nUser Request:\n{prompt}"
    for api_key in [GEMINI_API_KEY_1, GEMINI_API_KEY_2]:
        if not api_key:
            continue

        for model in GEMINI_MODELS:
            print(f"🔍 Trying {model} with key ending {api_key[-6:]}")
            try:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent?key={api_key}"
                )
                payload = {"contents": [{"parts": [{"text": combined_prompt}]}]}
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=40,
                )

                if response.status_code == 200:
                    data = response.json()
                    text = (
                        data.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                    )
                    if text:
                        print(f"✅ Success with {model}")
                        return text.strip()
                    print(f"⚠️ Empty response from {model}")
                else:
                    print(f"❌ {model} failed ({response.status_code})")

            except Exception as e:
                print(f"⚠️ {model} error: {e}")

            time.sleep(2)

    print("❌ All Gemini models and API keys failed.")
    return "⚠️ No AI response (Gemini rotation + keys failed)."


def ask_ai(prompt):
    """Gemini-only feedback system."""
    system_prompt = """
You are a world-class web design and front-end development expert.
Your task is to CRITIQUE and IMPROVE websites with professional precision.

Always:
- Be concise, confident, and specific.
- Use bullet points or numbered lists for clarity.
- Include short example snippets (HTML, CSS, JS).
- Do NOT explain what CSS is.
- Focus on design aesthetics, responsiveness, accessibility, and interactivity.

Format your reply exactly like this:

🧠 **AI Feedback**
1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]

💡 **Example Fixes**
```css
/* Example improvement */
```
"""
    return ask_gemini(prompt, system_prompt)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "environment": "Render" if IS_RENDER else "Local",
        "message": "Refactr Gemini-only backend running"
    })


@app.route("/analyze/url", methods=["POST"])
def analyze_url():
    """Analyze a URL and return AI-powered design feedback."""
    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.string if soup.title else "No title"
        text = " ".join([p.get_text() for p in soup.find_all("p")])[:2000]
        css_links = [
            link["href"]
            for link in soup.find_all("link", rel="stylesheet")
            if link.get("href")
        ]

        css_content = ""
        if css_links:
            css_url = urljoin(url, css_links[0])
            try:
                css_response = requests.get(css_url, timeout=5)
                css_content = css_response.text[:2000]
            except:
                css_content = "⚠️ Could not fetch external CSS."

        prompt = f"""
Analyze this website's front-end design and give focused improvements.

Title: {title}
Text: {text}
CSS Snippet: {css_content}

Focus your feedback on:
- Layout, spacing, color balance, and typography
- Responsiveness for mobile and desktop
- Interactivity (hover, transitions, animations)
- Accessibility (contrast, font sizing, alt tags)
"""

        ai_summary = ask_ai(prompt)

        return jsonify({
            "url": url,
            "title": title,
            "ai_analysis": ai_summary
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001 if not IS_RENDER else 10000))
    app.run(host="0.0.0.0", port=port)