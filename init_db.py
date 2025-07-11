from app import app, db, OlympiadEvent


with app.app_context():
    db.session.query(OlympiadEvent).delete()
    db.session.commit()


with app.app_context():
    db.drop_all()
    db.create_all()
