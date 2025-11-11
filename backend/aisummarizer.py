import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_1")
MODEL = "gemini-2.0-flash"

def analyze_with_ai(dom_snapshot: str, test_results: list) -> str:
    """
    Sends the DOM snapshot and functional test logs to Gemini
    and returns an AI-generated summary of what the page does.
    """

    if not GEMINI_API_KEY:
        return "⚠️ Missing GEMINI_API_KEY_1 in environment. Add it to your .env file."

    # Create a well-structured, detailed prompt
    prompt = f"""
You are an expert web analyst AI. Analyze the following website's HTML DOM
and test log, and explain what this page seems to do.

Be concise and factual, but also infer functionality intelligently.
If the site seems to be a game, describe the likely game rules and logic.

---
DOM Snapshot (truncated):
{dom_snapshot[:7000]}
---
Test Log:
{chr(10).join(test_results[:50])}
---

Please summarize:
1. What kind of website this is (game, form, dashboard, etc.)
2. What actions the user can perform
3. The possible goal or purpose of the page
4. If it looks like a game, describe the gameplay and rules
5. Mention broken or missing features (if any)

Format your response as a clear, numbered analysis.
"""

    try:
        # Build Gemini REST endpoint
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{MODEL}:generateContent?key={GEMINI_API_KEY}"
        )
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        print(f"🔄 Sending AI request to Gemini ({len(dom_snapshot)} chars of DOM)...")
        response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            res_json = response.json()
            ai_text = (
                res_json.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "⚠️ No AI response received.")
            )
            print("✅ AI analysis received successfully")
            return ai_text
        else:
            error_msg = f"⚠️ Gemini API Error {response.status_code}: {response.text[:200]}"
            print(error_msg)
            return error_msg

    except Exception as e:
        error_msg = f"⚠️ AI summarization failed: {str(e)}"
        print(error_msg)
        return error_msg