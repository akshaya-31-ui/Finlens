import os
from flask import Flask, request, jsonify, send_from_directory
from analyzer import analyze, llm_enabled

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
HERE = os.path.dirname(__file__)

@app.get("/")
def home(): return send_from_directory("static", "index.html")

@app.get("/api/health")
def health(): return jsonify(ok=True, llm=llm_enabled())

@app.post("/api/analyze")
def run():
    strategy = request.form.get("strategy", "zero_shot")
    try:
        if request.form.get("sample"):
            data = open(os.path.join(HERE, "samples", "northwind_annual_report.pdf"), "rb").read()
        else:
            f = request.files.get("file")
            if not f or not f.filename.lower().endswith(".pdf"):
                return jsonify(error="Choose a PDF file to analyse."), 400
            data = f.read()
        return jsonify(analyze(data, strategy))
    except ValueError as e: return jsonify(error=str(e)), 422
    except Exception as e: return jsonify(error=f"Could not read this PDF ({type(e).__name__})."), 500

@app.errorhandler(413)
def too_big(_): return jsonify(error="File is larger than 25 MB."), 413

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n  Finlens is running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
