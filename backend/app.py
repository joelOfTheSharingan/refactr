import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from styleanalyzer import analyze_website
from testfunctionality import test_site_functionality
from logictester import test_html_logic

# --- Setup ---
load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "environment": "Render" if os.getenv("RENDER") else "Local",
        "message": "Modular Refactr backend running"
    })


@app.route("/analyze/url", methods=["POST"])
def analyze_url():
    """Analyze website front-end style using Gemini."""
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    result = analyze_website(url)
    return jsonify(result)


@app.route("/test/functionality", methods=["POST"])
def functionality_test():
    """(Placeholder) Test core functionality of a website."""
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    result = test_site_functionality(url)
    return jsonify(result)


@app.route("/test/logic", methods=["POST"])
def logic_test():
    """(Placeholder) Test HTML logic or interactivity."""
    data = request.get_json()
    html = data.get("html")
    if not html:
        return jsonify({"error": "No HTML provided"}), 400

    result = test_html_logic(html)
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
