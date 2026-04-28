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
            page.goto("https://perchance.org/5he1ivtfwh", wait_until="networkidle", timeout=60000)
            time.sleep(15)  # più tempo per Turnstile
            
            # Dump completo del localStorage per vedere cosa c'è
            all_storage = page.evaluate("""
                () => {
                    let items = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        items[key] = localStorage.getItem(key);
                    }
                    return items;
                }
            """)
            
            print("LocalStorage completo:", all_storage)
            
            # Cerca userKey con nomi alternativi
            user_key = (
                all_storage.get("userKey") or
                all_storage.get("user_key") or
                all_storage.get("uk") or
                ""
            )
            
            cookies = context.cookies()
            print("Cookies:", [c["name"] for c in cookies])
            cf = next((c["value"] for c in cookies if c["name"] == "cf_clearance"), "")
            
        except Exception as e:
            print("Errore:", str(e))
            browser.close()
            return jsonify({"error": str(e)}), 500
        
        browser.close()
        
        # Ritorna tutto per debug
        return jsonify({
            "userKey": user_key,
            "cfClearance": cf,
            "allStorage": all_storage,
            "cookies": [c["name"] for c in cookies]
        })
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)