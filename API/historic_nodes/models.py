from flask_sqlalchemy import SQLAlchemy
from DB import db

class ThornodeMonitorHistoric(db.Model):
    __tablename__ = 'thornode_monitor_historic'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    node_address = db.Column(db.String(255), nullable=False)
    active_block_height = db.Column(db.Integer, nullable=True)
    bond_providers = db.Column(db.Text, nullable=True)
    bond = db.Column(db.BigInteger, nullable=True)
    current_award = db.Column(db.BigInteger, nullable=True)
    slash_points = db.Column(db.Integer, nullable=True)
    forced_to_leave = db.Column(db.Boolean, nullable=True)
    requested_to_leave = db.Column(db.Boolean, nullable=True)
    bond_address = db.Column(db.String(255), nullable=True)
    preflight_status = db.Column(db.String(1024), nullable=True)
    status = db.Column(db.String(255), nullable=True)
    status_since = db.Column(db.Integer, nullable=True)
    version = db.Column(db.String(63), nullable=True)
    ip_address = db.Column(db.String(63), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    isp = db.Column(db.String(255), nullable=True)
    rpc = db.Column(db.String(1023), nullable=True)
    bifrost = db.Column(db.String(63), nullable=True)
    bondProvidersString = db.Column(db.String(512), nullable=True)
    churnHeight = db.Column(db.Integer, nullable=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    maxNodes = db.Column(db.Integer, nullable=False, default=0)
    award_per_block = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f"<ThornodeMonitorHistoric id={self.id} node_address={self.node_address}>"

    def to_dict(self):
        return {
            'id': self.id,
            'node_address': self.node_address,
            'active_block_height': self.active_block_height,
            'bond_providers': self.bond_providers,
            'bond': self.bond,
            'current_award': self.current_award,
            'slash_points': self.slash_points,
            'forced_to_leave': self.forced_to_leave,
            'requested_to_leave': self.requested_to_leave,
            'bond_address': self.bond_address,
            'preflight_status': self.preflight_status,
            'status': self.status,
            'status_since': self.status_since,
            'version': self.version,
            'ip_address': self.ip_address,
            'location': self.location,
            'isp': self.isp,
            'rpc': self.rpc,
            'bifrost': self.bifrost,
            'bondProvidersString': self.bondProvidersString,
            'churnHeight': self.churnHeight,
            'position': self.position,
            'maxNodes': self.maxNodes,
            'award_per_block': self.award_per_block
        }