from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class EasterEggRedemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    redeemed_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    
    # Beziehung zum User-Modell
    user = db.relationship('User', backref=db.backref('easter_eggs', lazy=True))

    def __repr__(self):
        return f'<EasterEggRedemption {self.user_id} - {self.code}>'