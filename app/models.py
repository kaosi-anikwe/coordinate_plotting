from . import db


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), nullable=False)
    plant_name = db.Column(db.String(50), nullable=False)

    def __init__(self, plant_name, user_id):
        self.user_id = user_id
        self.plant_name = plant_name

    def insert(self):
        db.session.add(self)
        db.session.commit(self)

    def update(self):
        db.session.commit(self)

    def delete(self):
        db.session.delete(self)
        db.session.commit(self)
