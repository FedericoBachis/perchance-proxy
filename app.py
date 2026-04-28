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
        
        user_key = ""
        
        try:
            # Intercetta le richieste di rete per catturare il userKey
            captured = {}
            
            def handle_request(request):
                if "checkUserVerificationStatus" in request.url:
                    print("Trovata richiesta verifica:", request.url)
                    # Estrai userKey dall'URL
                    for param in request.url.split("&"):
                        if param.startswith("userKey="):
                            captured["userKey"] = param.split("=")[1]
                            print("userKey catturato:", captured["userKey"])

            def handle_response(response):
                if "verifyUser" in response.url:
                    try:
                        body = response.text()
                        print("verifyUser risposta:", body)
                        if "token" in response.url:
                            # Estrai token dall'URL
                            for param in response.url.split("&"):
                                if "token=" in param:
                                    captured["token"] = param.split("=")[1]
                    except:
                        pass

            page.on("request", handle_request)
            page.on("response", handle_response)

            # Carica prima la pagina principale per ottenere cf_clearance
            page.goto("https://perchance.org/5he1ivtfwh", wait_until="networkidle", timeout=60000)
            time.sleep(5)
            
            # Poi carica l'embed dove viene generato il userKey
            page.goto("https://image-generation.perchance.org/embed", wait_until="networkidle", timeout=60000)
            time.sleep(15)
            
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
            
            print("LocalStorage embed:", all_storage)
            print("Captured:", captured)
            
            user_key = captured.get("userKey", "")
            
            cookies = context.cookies()
            cf = next((c["value"] for c in cookies if c["name"] == "cf_clearance"), "")
            
        except Exception as e:
            print("Errore:", str(e))
            browser.close()
            return jsonify({"error": str(e)}), 500
        
        browser.close()
        
        return jsonify({
            "userKey": user_key,
            "cfClearance": cf,
            "allStorage": all_storage,
            "captured": captured
        })
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)