import asyncio
import os
import time
from typing import List, Dict, Any
import requests
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser

try:
    from aisummarizer import analyze_with_ai
    print("✅ aisummarizer module imported successfully")
except Exception as e:
    print(f"⚠️ Failed to import aisummarizer: {e}")
    analyze_with_ai = None

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_1")
GEMINI_MODEL = "gemini-2.0-flash"


async def _safe_click(page: Page, el, timeout: int = 2000) -> Dict[str, Any]:
    """Click an element, record DOM before/after, and return structured details."""
    entry: Dict[str, Any] = {}
    try:
        entry["outerHTML"] = (await page.evaluate("(el) => el.outerHTML", el))[:800]
    except Exception:
        entry["outerHTML"] = "<outerHTML-error>"

    try:
        entry["dom_before_click"] = (await page.content())[:5000]
    except Exception:
        entry["dom_before_click"] = "<before-fail>"

    try:
        await page.evaluate("(el) => el.scrollIntoView({block: 'center'})", el)
        await el.click(timeout=timeout)
        await page.wait_for_load_state("networkidle", timeout=10000)
        await page.wait_for_timeout(500)
        entry["result"] = "clicked"
    except Exception as e:
        entry["result"] = "error"
        entry["error"] = str(e)[:300]

    try:
        entry["current_url"] = page.url
        entry["dom_after_click"] = (await page.content())[:5000]
        body_text = await page.evaluate("() => document.body.innerText")
        entry["body_snippet"] = (body_text or "")[:1000].replace("\n", " ")
    except Exception:
        entry["body_snippet"] = ""

    return entry


async def test_basic_functionality(url: str, username: str = None, password: str = None, click_limit: int = 20):
    """Visit a page, explore links/buttons, record DOM changes, and summarize."""
    results, element_log = [], []
    start_time = time.time()
    dom_before, dom_after = "", ""

    try:
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
            page = await browser.new_page()
            print(f"🔄 Opening: {url}")
            await page.goto(url, timeout=30000)

            # Record initial DOM snapshot
            dom_before = await page.content()
            results.append("✅ Initial page loaded successfully")

            # Gather all clickable elements
            selectors = [
                "button", "a[href]", "input[type='button']",
                "input[type='submit']", "[role='button']"
            ]
            found_elements = []
            for sel in selectors:
                try:
                    found_elements.extend(await page.query_selector_all(sel))
                except Exception:
                    pass

            results.append(f"ℹ️ Found {len(found_elements)} clickable elements")

            seen_outer = set()
            count = 0

            for el in found_elements:
                if count >= click_limit:
                    break
                try:
                    outer_html = await page.evaluate("(el) => el.outerHTML", el)
                except Exception:
                    continue

                sig = (outer_html or "")[:300]
                if sig in seen_outer:
                    continue
                seen_outer.add(sig)

                entry = await _safe_click(page, el)
                element_log.append(entry)
                count += 1

                if entry["result"] == "clicked":
                    results.append(f"✅ Clicked element #{count} at {entry.get('current_url','(no url)')}")
                    # Capture what’s visible on that page (useful for “next page” detection)
                    snippet = entry.get("body_snippet", "")[:200]
                    results.append(f"🧭 Page content snippet: {snippet}")
                else:
                    results.append(f"⚠️ Failed to click element #{count}: {entry.get('error','unknown')}")

            dom_after = await page.content()
            results.append(f"ℹ️ Interaction sweep complete: {count} elements clicked")
            await browser.close()

    except Exception as e:
        results.append(f"❌ Fatal error: {e}")
        print(f"❌ Fatal error: {e}")

    # Basic diff stats
    diff_summary = {
        "before_length": len(dom_before),
        "after_length": len(dom_after),
        "length_delta": len(dom_after) - len(dom_before)
    }

    # Prepare for AI summarization
    ai_input_dom = dom_after[:15000]
    ai_input_log = results + [
        "\nFirst few interactions:",
        *[(e.get("body_snippet", "")[:500]) for e in element_log[:5]]
    ]

    ai_summary_text = None
    try:
        print("🤖 Sending to AI summarizer...")
        if analyze_with_ai:
            ai_summary_text = analyze_with_ai(ai_input_dom, ai_input_log)
        else:
            ai_summary_text = _analyze_with_gemini_rest(ai_input_dom, ai_input_log)
    except Exception as e:
        ai_summary_text = f"⚠️ AI summarization failed: {e}"

    total_time = round(time.time() - start_time, 2)
    return {
        "url": url,
        "status": "completed" if any('✅' in r for r in results) else "failed",
        "duration_seconds": total_time,
        "summary": {
            "results": results,
            "dom_diff": diff_summary,
            "element_log_count": len(element_log),
            "element_log_sample": element_log[:5]
        },
        "ai_analysis": ai_summary_text
    }


def _analyze_with_gemini_rest(dom_snapshot: str, test_results: List[str]) -> str:
    """Fallback Gemini REST summarization."""
    key = GEMINI_API_KEY
    if not key:
        return "⚠️ Missing GEMINI_API_KEY_1 in environment."

    prompt = (
        "You are an expert website analyst. Based on the DOM snapshot and interaction log, "
        "summarize what the site does, what actions the automation performed, what changed after clicks, "
        "and describe what each page contains. Include any broken/missing features.\n\n"
        f"DOM:\n{dom_snapshot[:9000]}\n\nLOG:\n{chr(10).join(test_results[:50])}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        if r.status_code == 200:
            j = r.json()
            return (
                j.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "⚠️ No Gemini response.")
            )
        else:
            return f"⚠️ Gemini error {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"⚠️ Gemini request failed: {e}"


def run_test(url: str, username: str = None, password: str = None):
    print(f"\n🚀 Running deep web test for {url}\n")
    result = asyncio.run(test_basic_functionality(url, username, password))
    print(f"\n✅ Test complete in {result['duration_seconds']}s\n")
    return result


if __name__ == "__main__":
    import json
    output = run_test("https://example.com")
    print(json.dumps(output, indent=2))
