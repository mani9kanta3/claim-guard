from app.extensions import db


class Hospital(db.Model):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(60))
    is_network = db.Column(db.Boolean, nullable=False, server_default=db.false())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "is_network": self.is_network,
        }
