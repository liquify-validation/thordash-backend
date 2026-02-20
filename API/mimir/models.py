from DB import db
import json


class MimirCache(db.Model):
    __tablename__ = 'mimir_cache'

    # Always a single row (id=1)
    id         = db.Column(db.Integer,  primary_key=True)
    data       = db.Column(db.Text,     nullable=True)   # Full JSON dict from THORNode
    updated_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return json.loads(self.data) if self.data else {}
