from DB import db
import json


class PoolCache(db.Model):
    __tablename__ = 'pool_cache'

    asset           = db.Column(db.String(255), primary_key=True)
    status          = db.Column(db.String(50),  nullable=True)
    asset_depth     = db.Column(db.BigInteger,  nullable=True)
    rune_depth      = db.Column(db.BigInteger,  nullable=True)
    pool_apy        = db.Column(db.Float,       nullable=True)
    asset_price_usd = db.Column(db.String(50),  nullable=True)
    volume_24h      = db.Column(db.BigInteger,  nullable=True)
    data            = db.Column(db.Text,        nullable=True)  # Full JSON from Midgard
    updated_at      = db.Column(db.DateTime,    nullable=True)

    def to_dict(self):
        return json.loads(self.data) if self.data else {}


class PoolStatsCache(db.Model):
    __tablename__ = 'pool_stats_cache'

    # Always a single row (id=1)
    id         = db.Column(db.Integer,  primary_key=True)
    data       = db.Column(db.Text,     nullable=True)   # Full JSON from Midgard /v2/stats
    updated_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return json.loads(self.data) if self.data else {}
