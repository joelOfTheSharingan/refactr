import asyncio
import os
import time
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser

# Try to import your external ai summarizer; fall back to local HTTP call if needed.
try:
    from aisummarizer import analyze_with_ai
    print("✅ aisummarizer module imported successfully")
except Exception as e:
    print(f"⚠️ Failed to import aisummarizer: {e}")
    analyze_with_ai = None

load_dotenv()

# If aisummarizer import failed, we'll use the direct Gemini REST call as a fallback.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_1")
GEMINI_MODEL = "gemini-2.0-flash"


async def _safe_click(page: Page, el, timeout: int = 2000) -> Dict[str, Any]:
    """Try to click an element and return a structured result (success/failure + snapshot)."""
    try:
        outer = await page.evaluate("(el) => el.outerHTML", el)
    except Exception:
        outer = "<outerHTML-ERR>"

    entry: Dict[str, Any] = {"outerHTML": (outer or "")[:800]}

    try:
        # Scroll into view and click
        await page.evaluate("(el) => el.scrollIntoView({block: 'center'})", el)
        await el.click(timeout=timeout)
        await page.wait_for_timeout(400)  # let micro-navigation happen
        entry["result"] = "clicked"
    except Exception as e:
        entry["result"] = "error"
        entry["error"] = str(e)[:300]

    # capture url and small DOM excerpt after click
    try:
        entry["current_url"] = page.url
        body_text = await page.evaluate("() => document.body.innerText")
        entry["body_snippet"] = (body_text or "")[:1000].replace("\n", " ")[:800]
    except Exception:
        entry["body_snippet"] = ""

    return entry


async def test_basic_functionality(url: str, username: str = None, password: str = None, click_limit: int = 50):
    """
    Visit a page, interact with many interactive elements, record what happens,
    and return results plus an AI summary (via aisummarizer or Gemini REST fallback).
    """
    results: List[str] = []
    element_log: List[Dict[str, Any]] = []
    dom_before = ""
    dom_after = ""
    start_time = time.time()

    try:
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=True,args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"])
            page = await browser.new_page()

            # optional: record console messages for debugging
            console_msgs = []
            page.on("console", lambda msg: console_msgs.append(f"{msg.type}: {msg.text}"))

            # load page
            print(f"🔄 Loading page: {url}")
            await page.goto(url, timeout=30000)
            results.append("✅ Page loaded successfully")
            dom_before = await page.content()

            # Optional login attempt if credentials provided
            if username and password:
                try:
                    user_field = await page.query_selector("input[type='text'], input[name*='user'], input[name*='email']")
                    pass_field = await page.query_selector("input[type='password']")
                    login_btn = await page.query_selector("button[type='submit'], button.login, input[type='submit']")
                    if user_field and pass_field and login_btn:
                        await user_field.fill(username)
                        await pass_field.fill(password)
                        await login_btn.click()
                        results.append("✅ Login attempt executed")
                        await page.wait_for_timeout(2000)
                    else:
                        results.append("⚠️ Login fields not detected")
                except Exception as e:
                    results.append(f"⚠️ Login attempt error: {e}")

            # collect interactive elements (de-duplicate by outerHTML snippet)
            selectors = [
                "button",
                "a[href]",
                "input[type='button']",
                "input[type='submit']",
                "input[type='checkbox']",
                "input[type='radio']",
                "[role='button']",
                "label[for]"
            ]
            found_elements = []
            for sel in selectors:
                try:
                    nodes = await page.query_selector_all(sel)
                    found_elements.extend(nodes)
                except Exception:
                    pass

            results.append(f"ℹ️ Found {len(found_elements)} interactive elements (raw)")
            print(f"📊 Found {len(found_elements)} interactive elements")

            # interact with elements but limit to avoid runaway loops
            count = 0
            seen_outer = set()
            for i, el in enumerate(found_elements):
                if count >= click_limit:
                    break
                try:
                    outer_html = await page.evaluate("(el) => el.outerHTML", el)
                except Exception:
                    outer_html = None

                # avoid clicking many duplicates
                signature = (outer_html or "")[:300]
                if signature in seen_outer:
                    continue
                seen_outer.add(signature)

                entry = await _safe_click(page, el)
                element_log.append(entry)

                if entry.get("result") == "clicked":
                    results.append(f"✅ Clicked element #{count+1}: {entry['outerHTML'][:120].replace(chr(10),' ')}")
                else:
                    results.append(f"⚠️ Element #{count+1} click failed: {entry.get('error','unknown')[:120]}")

                count += 1

            # capture after-interaction state
            dom_after = await page.content()
            results.append(f"ℹ️ Interaction sweep: {count} elements processed")
            print(f"✅ Interaction sweep complete: {count} elements tested")
            
            # optionally inspect for obvious errors
            body_lower = (await page.evaluate("() => document.body.innerText")).lower()
            if "error" in body_lower or "exception" in body_lower:
                results.append("⚠️ Page text contains 'error' or 'exception' after interactions")

            # gather a short console summary
            if console_msgs:
                results.append(f"ℹ️ Console messages captured: {len(console_msgs)}")
                # keep first few console lines in details
                element_log.append({"console": console_msgs[:20]})

            await browser.close()

    except Exception as e:
        error_msg = f"❌ Fatal automation error: {str(e)}"
        results.append(error_msg)
        print(error_msg)

    # quick DOM diff summary (simple — length + changed substrings count)
    diff_summary = {
        "before_length": len(dom_before),
        "after_length": len(dom_after),
        "length_delta": len(dom_after) - len(dom_before)
    }

    # Prepare payload for AI
    ai_input_dom = dom_after if len(dom_after) < 15000 else dom_after[:15000]
    ai_input_log = results + [f"\nElement details (first {min(10, len(element_log))}):"] + [
        (e.get("outerHTML","")[:500].replace("\n"," ") if isinstance(e, dict) else str(e)) for e in element_log[:10]
    ]

    # Call external analyzer if available
    ai_summary_text = None
    try:
        print("🤖 Requesting AI analysis...")
        if analyze_with_ai:
            ai_summary_text = analyze_with_ai(ai_input_dom, ai_input_log)
        else:
            # fallback: direct Gemini REST call
            print("⚠️ Using fallback Gemini REST call")
            ai_summary_text = _analyze_with_gemini_rest(ai_input_dom, ai_input_log)
    except Exception as e:
        ai_summary_text = f"⚠️ AI summarization failed: {e}"
        print(ai_summary_text)

    total_time = time.time() - start_time
    
    return {
        "url": url,
        "status": "completed" if any(r.startswith("✅") for r in results) else "failed",
        "duration_seconds": round(total_time, 2),
        "summary": {
            "results": results,
            "element_log_count": len(element_log),
            "element_log_sample": element_log[:10],
            "dom_diff": diff_summary
        },
        "ai_analysis": ai_summary_text
    }


def _analyze_with_gemini_rest(dom_snapshot: str, test_results: List[str]) -> str:
    """Fallback direct Gemini REST call if aisummarizer module is not present."""
    key = GEMINI_API_KEY
    model = GEMINI_MODEL
    if not key:
        return "⚠️ Missing GEMINI_API_KEY_1 in environment for fallback Gemini call."

    prompt = (
        "You are an expert web analyst. Given the DOM snapshot and an automated interaction log, "
        "explain the website's purpose, what user actions are supported, what changed after clicks, "
        "and note broken or missing features. If it's a game, describe plausible rules.\n\n"
        f"DOM (truncated):\n{(dom_snapshot or '')[:9000]}\n\n"
        f"Interaction log (truncated):\n{chr(10).join(test_results[:50])}\n\n"
        "Provide a concise, numbered summary with reasoning.\n"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        print("🔄 Sending fallback Gemini REST request...")
        r = requests.post(url, headers=headers, json=data, timeout=60)
        if r.status_code == 200:
            j = r.json()
            ai_text = (
                j.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "⚠️ No AI response.")
            )
            print("✅ Fallback AI response received")
            return ai_text
        else:
            error_msg = f"⚠️ Gemini fallback error {r.status_code}: {r.text[:200]}"
            print(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"⚠️ Gemini REST call failed: {e}"
        print(error_msg)
        return error_msg


def run_test(url: str, username: str = None, password: str = None):
    """Synchronous wrapper usable from Flask routes."""
    print(f"\n{'='*60}")
    print(f"🚀 Starting functionality test for: {url}")
    print(f"{'='*60}\n")
    
    result = asyncio.run(test_basic_functionality(url, username, password))
    
    print(f"\n{'='*60}")
    print(f"✅ Test completed in {result['duration_seconds']}s")
    print(f"{'='*60}\n")
    
    return result


# quick manual test when run directly
if __name__ == "__main__":
    import json
    out = run_test("https://example.com")
    print(json.dumps(out, indent=2))