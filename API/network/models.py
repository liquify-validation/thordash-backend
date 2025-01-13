from DB import db
import json

class ThornodeMonitorGlobal(db.Model):
    __tablename__ = 'thornode_monitor_global'

    primary_key = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maxHeight = db.Column(db.Integer, nullable=True)
    retiring = db.Column(db.Boolean, nullable=True)
    coingecko = db.Column(db.String(4095), nullable=True)
    lastChurn = db.Column(db.Integer, nullable=True)
    secondsPerBlock = db.Column(db.String(255), nullable=True)
    churnInterval = db.Column(db.Integer, nullable=True)
    BadValidatorRedline = db.Column(db.Integer, nullable=True)
    maxEffectiveStake = db.Column(db.BigInteger, nullable=True)
    halts = db.Column(db.String(4095), nullable=True)

    def __repr__(self):
        return (f"<ThornodeMonitorGlobal("
                f"primary_key={self.primary_key}, "
                f"maxHeight={self.maxHeight}, "
                f"retiring={self.retiring}, "
                f"coingecko={self.coingecko}, "
                f"lastChurn={self.lastChurn}, "
                f"secondsPerBlock={self.secondsPerBlock}, "
                f"churnInterval={self.churnInterval}, "
                f"BadValidatorRedline={self.BadValidatorRedline}, "
                f"maxEffectiveStake={self.maxEffectiveStake}, "
                f"halts={self.halts})>")

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        return {
            "primary_key": self.primary_key,
            "maxHeight": self.maxHeight,
            "retiring": self.retiring,
            "coingecko": self.coingecko,
            "lastChurn": self.lastChurn,
            "secondsPerBlock": self.secondsPerBlock,
            "churnInterval": self.churnInterval,
            "BadValidatorRedline": self.BadValidatorRedline,
            "maxEffectiveStake": self.maxEffectiveStake,
            "halts": self.halts,  # This will be a string in your case
        }

    def to_json(self):
        """Convert the model instance to a JSON string."""
        return json.dumps(self.to_dict())