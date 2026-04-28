from flask import Flask, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import time

app = Flask(__name__)
CORS(app)

@app.route("/getkey")
def get_key():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0"
        )
        page = context.new_page()
        
        try:
            page.goto("https://perchance.org/5he1ivtfwh", wait_until="networkidle", timeout=30000)
            time.sleep(8)  # aspetta Turnstile
            
            user_key = page.evaluate("localStorage.getItem('userKey') || ''")
            
            cookies = context.cookies()
            cf = next((c["value"] for c in cookies if c["name"] == "cf_clearance"), "")
            
        except Exception as e:
            browser.close()
            return jsonify({"error": str(e)}), 500
        
        browser.close()
        
        if not user_key:
            return jsonify({"error": "userKey non trovato"}), 500
            
        return jsonify({
            "userKey": user_key,
            "cfClearance": cf
        })

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)