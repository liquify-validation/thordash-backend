from flask_sqlalchemy import SQLAlchemy
from DB import db

class ThornodeMonitorGlobalHistoric(db.Model):
    __tablename__ = 'thornode_monitor_global_historic'

    churnHeight = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maxEffectiveStake = db.Column(db.BigInteger, nullable=False, default=0)
    totalBondedRune = db.Column(db.BigInteger, nullable=False, default=0)
    thorPrice = db.Column(db.String(45), nullable=True)
    date = db.Column(db.String(12), nullable=True)

    def __repr__(self):
        return f"<ThornodeMonitorGlobalHistoric churnHeight={self.churnHeight}>"

    def to_dict(self):
        return {
            'churnHeight': self.churnHeight,
            'maxEffectiveStake': self.maxEffectiveStake,
            'totalBondedRune': self.totalBondedRune,
            'thorPrice': self.thorPrice,
            'date': self.date
        }

class PriceData(db.Model):
    __tablename__ = 'price_data'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    def __repr__(self):
        return f"<PriceData(id={self.id}, date={self.date}, price={self.price})>"

    def to_dict(self):
        return {
            "date": self.date.isoformat(),  # Converts the date to ISO format string
            "price": self.price
        }