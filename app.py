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
            captured = {}

            def handle_request(request):
                if "checkUserVerificationStatus" in request.url:
                    print("TROVATO checkUserVerificationStatus:", request.url)
                    for param in request.url.split("&"):
                        if "userKey=" in param:
                            captured["userKey"] = param.split("=")[1]

            page.on("request", handle_request)

            # Carica la pagina e aspetta che appaia la richiesta
            page.goto("https://perchance.org/5he1ivtfwh", timeout=60000)
            
            # Aspetta fino a 30 secondi che il userKey venga catturato
            for i in range(30):
                if captured.get("userKey"):
                    print(f"userKey trovato dopo {i}s")
                    break
                time.sleep(1)

            cookies = context.cookies()
            cf = next((c["value"] for c in cookies if c["name"] == "cf_clearance"), "")

        except Exception as e:
            print("Errore:", str(e))
            browser.close()
            return jsonify({"error": str(e)}), 500

        browser.close()

        return jsonify({
            "userKey": captured.get("userKey", ""),
            "cfClearance": cf
        })
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)