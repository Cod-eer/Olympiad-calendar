from app import app, db, OlympiadEvent # make sure this line is present!

with app.app_context():
    db.create_all()
