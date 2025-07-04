from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from pathlib import Path
import os
import time
import backend.app.scraper as scraper
import requests

load_dotenv(dotenv_path=Path("config/.env"))




app = Flask(
    __name__,
    template_folder="frontend/source/pages/templates",
    static_folder="frontend/static",
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class OlympiadEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "date": self.date,
        }

    def __repr__(self):
        return '<Event %r>' % self.id


app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.get_json()
        url = data.get("url", "")
        try:
            result = scraper.scrape_return_dict(url, app.config["OPENAI_API_KEY"])
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        return render_template("landing.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="127.0.0.1")
