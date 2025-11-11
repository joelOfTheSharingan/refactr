import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv

load_dotenv()

# --- Gemini API Keys ---
GEMINI_API_KEY_1 = os.getenv("GEMINI_API_KEY_1")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")

# --- Gemini Models ---
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-pro",
    "gemini-2.0-flash-lite",
]


def ask_gemini(prompt, system_prompt=""):
    """Try Gemini models in order using both keys."""
    combined_prompt = f"{system_prompt}\nUser Request:\n{prompt}"

    for api_key in [GEMINI_API_KEY_1, GEMINI_API_KEY_2]:
        if not api_key:
            continue

        for model in GEMINI_MODELS:
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

    return "⚠️ No valid Gemini response."


def ask_ai(prompt):
    """Gemini-only feedback system."""
    system_prompt = """
You are a world-class web design and front-end development expert.
Your task is to CRITIQUE and IMPROVE websites with professional precision.

Always:
- Be concise and confident.
- Use bullet points or numbered lists.
- Include short example CSS/HTML/JS fixes.
- Focus on visual design, responsiveness, and interactivity.

Format strictly as:

🧠 **AI Feedback**
1. [recommendation 1]
2. [recommendation 2]

💡 **Example Fixes**
```css
/* Example improvement */
```
"""
    return ask_gemini(prompt, system_prompt)


def analyze_website(url):
    """Analyze a URL and return Gemini-powered feedback."""
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
            except Exception:
                css_content = "⚠️ Could not fetch external CSS."

        prompt = f"""
Analyze this website's front-end design and suggest improvements.

Title: {title}
Text: {text}
CSS Snippet: {css_content}

Focus on:
- Layout and color balance
- Typography and spacing
- Mobile responsiveness
- Interactivity and animations
- Accessibility
"""

        ai_summary = ask_ai(prompt)

        return {
            "url": url,
            "title": title,
            "ai_analysis": ai_summary,
        }

    except Exception as e:
        return {"error": str(e)}