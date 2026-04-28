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

            def handle_response(response):
                try:
                    if "verifyUser" in response.url:
                        print("verifyUser URL:", response.url)
                        body = response.text()
                        print("verifyUser body:", body)
                        # La risposta dovrebbe contenere il userKey
                        if "userKey" in body:
                            import re
                            match = re.search(r'"userKey"\s*:\s*"([^"]+)"', body)
                            if match:
                                captured["userKey"] = match.group(1)
                                print("✅ userKey catturato:", captured["userKey"])
                    
                    if "checkUserVerificationStatus" in response.url:
                        print("checkUserVerification URL:", response.url)
                        body = response.text()
                        print("checkUserVerification body:", body)

                except Exception as e:
                    print("Errore handler:", e)

            page.on("response", handle_response)

            page.goto("https://perchance.org/5he1ivtfwh", timeout=60000)
            
            # Aspetta fino a 45 secondi
            for i in range(45):
                if captured.get("userKey"):
                    print(f"✅ userKey trovato dopo {i}s")
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
            "cfClearance": cf,
            "captured": captured
        })
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)