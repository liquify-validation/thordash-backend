from DB import db
import json


class QueueCache(db.Model):
    __tablename__ = 'queue_cache'

    # Always a single row (id=1)
    id             = db.Column(db.Integer,  primary_key=True)
    outbound_count = db.Column(db.Integer,  nullable=True)
    scheduled_count= db.Column(db.Integer,  nullable=True)
    swap_count     = db.Column(db.Integer,  nullable=True)
    outbound_data  = db.Column(db.Text,     nullable=True)  # JSON array of outbound txs
    scheduled_data = db.Column(db.Text,     nullable=True)  # JSON array of scheduled txs
    updated_at     = db.Column(db.DateTime, nullable=True)

    def summary(self):
        return {
            'outbound':  self.outbound_count,
            'scheduled': self.scheduled_count,
            'swap':      self.swap_count,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def outbound_list(self):
        return json.loads(self.outbound_data) if self.outbound_data else []

    def scheduled_list(self):
        return json.loads(self.scheduled_data) if self.scheduled_data else []
