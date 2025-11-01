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

# Allow requests from your GitHub Pages and local dev environment
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://joelofthesharingan.github.io",
            "http://localhost:5173"
        ]
    }
})

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# List of free models to rotate through
FREE_MODELS = [
    "agentica-org/deepcoder-14b-preview:free",
    "google/gemma-2-9b-it:free",
    "tngtech/deepseek-r1t2-chimera:free",
    "mistralai/mistral-7b-instruct:free",
    "deepseek/deepseek-coder:free"
]

last_successful_model = None  # Remember the last working model


def ask_ai(prompt):
    """Try several free models until one works, formatted for design feedback."""
    global last_successful_model

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

    model_order = [last_successful_model] + FREE_MODELS if last_successful_model else FREE_MODELS

    for model in model_order:
        if not model:
            continue

        print(f"🧠 Trying model: {model}")
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                }),
                timeout=40
            )

            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")

            if content:
                last_successful_model = model
                print(f"✅ Success with {model}")

                # Ensure the format is consistent
                if "🧠" not in content:
                    content = f"🧠 **AI Feedback**\n{content}\n\n💡 **Example Fixes**\n```css\n/* Add your improvements here */\n```"

                return content.strip()

            print(f"❌ Empty response from {model}")

        except Exception as e:
            print(f"⚠️ Model {model} failed:", e)

        time.sleep(4)  # Slight delay between retries

    return "⚠️ No AI response (all free models failed or rate-limited)."


@app.route("/", methods=["GET"])
def home():
    """Simple health-check route for Render."""
    return jsonify({"message": "Refactr backend running"}), 200


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
        css_links = [link["href"] for link in soup.find_all("link", rel="stylesheet") if link.get("href")]

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)