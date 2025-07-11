from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from pathlib import Path
import os
import time
from backend.app.scraper import scrape_return_dict
import requests

load_dotenv(dotenv_path=Path("config/.env"))




app = Flask(
    __name__,
    template_folder="frontend/source/templates",
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
    action = db.Column(db.String(200), nullable=False)
    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "date": self.date,
            "action": self.action,
        }

    def __repr__(self):
        return '<Event %r>' % self.id


app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

@app.route("/")
def landing():
    events = OlympiadEvent.query.all()
    return render_template("landing.html", events=events)


@app.route("/parse", methods=["POST"])
def parse():
    data = request.get_json()
    url = data.get("url", "")
    try:
        result = scrape_return_dict(url, app.config["OPENAI_API_KEY"])
        return jsonify(result)
    except Exception as e:
        app.logger.error("An error occurred during parsing: %s", str(e))
        return jsonify({"error": "An internal error occurred"})


@app.route("/results")

def results():
    return render_template("results.html")


@app.route("/add_event", methods=["POST"])

def add_event():
    try:
        data = request.get_json()
        url = data.get("url", "")
        title = data.get("name", ["Unnamed Event"])[0]

        existing = OlympiadEvent.query.filter_by(title=title).first()
        if existing:
            db.session.commit()
            return jsonify({"success": True})

        dates = list(data.get("dates", [""]))
        for date_str in dates:
            date_str = str(date_str)
            if "–" in date_str:
                parsed_date, action = map(str.strip, date_str.split("–", 1))
            else:
                parsed_date, action = date_str, ""

            event = OlympiadEvent(url=url, title=title, date=parsed_date, action=action)
            db.session.add(event)
        db.session.commit()

        return jsonify({"success": True})
    except Exception as e:
        app.logger.error("An error occurred while adding an event: %s", str(e))
        return jsonify({"success": False, "error": "An internal error occurred"})
#ADD a datetime transformation

if __name__ == "__main__":
    app.run(debug=FALSE, port=5000, host="127.0.0.1")
