from flask import Flask, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import time
import sys
import os
import re

os.environ["PYTHONUNBUFFERED"] = "1"

app = Flask(__name__)
CORS(app)

def log(msg):
    print(msg, flush=True)
    sys.stdout.flush()

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

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
            captured = {}

            def handle_response(response):
                try:
                    url = response.url
                    if "verifyUser" in url or "checkUser" in url or "userKey" in url:
                        log(f"📡 Response intercettata: {url}")
                        body = response.text()
                        log(f"📄 Body: {body[:200]}")
                        if "userKey" in body:
                            match = re.search(r'"userKey"\s*:\s*"([^"]+)"', body)
                            if match:
                                captured["userKey"] = match.group(1)
                                log(f"✅ userKey: {captured['userKey']}")
                except Exception as e:
                    log(f"Handler error: {e}")

            def handle_request(req):
                url = req.url
                if "verifyUser" in url or "checkUser" in url or "image-generation" in url:
                    log(f"➡️ Request: {url[:150]}")

            page.on("response", handle_response)
            page.on("request", handle_request)

            log("🌐 Carico pagina...")
            page.goto("https://perchance.org/5he1ivtfwh", timeout=60000)
            log("✅ Pagina caricata")

            for i in range(45):
                if captured.get("userKey"):
                    log(f"✅ Done in {i}s")
                    break
                if i % 5 == 0:
                    log(f"⏳ Attendo... {i}s")
                time.sleep(1)

            cookies = context.cookies()
            cf = next((c["value"] for c in cookies if c["name"] == "cf_clearance"), "")
            log(f"🍪 cf_clearance: {'trovato' if cf else 'NON trovato'}")

        except Exception as e:
            log(f"❌ Errore: {str(e)}")
            browser.close()
            return jsonify({"error": str(e)}), 500

        browser.close()

        return jsonify({
            "userKey": captured.get("userKey", ""),
            "cfClearance": cf,
            "captured": captured
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)