from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from pathlib import Path
import os
import backend.app.scraper as scraper
import requests

load_dotenv(dotenv_path=Path("config/.env"))



app = Flask(
    __name__,
    template_folder="frontend/source/pages/templates",
    static_folder="frontend/static",
)

app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
@app.route("/", methods=["GET"])
def index():
    data = {"error": None, "message": "Hello from Flask!"}
    return render_template("landing.html", data=data)

@app.route("/parse_data", methods=["POST"])
def parse_data():
    print("Content-Type:", type(request))
    print("Raw data:", request.data)  # raw bytes of body
    data = request.get_json(silent=True)
    #url = data.get("url", "")
    #try:
    #    result = scraper.scrape_return_dict(url, app.config["OPENAI_API_KEY"])
    #    return jsonify(result)
    #except Exception as e:
    #    return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)





if __name__ == "__main__":
    app.run(debug=True, port=5000, host="127.0.0.1")
