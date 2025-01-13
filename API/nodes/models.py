from DB import db
import json

class ThornodeMonitor(db.Model):
    __tablename__ = 'thornode_monitor'

    node_address = db.Column(db.String(255), primary_key=True, nullable=False)
    active_block_height = db.Column(db.Integer, nullable=True)
    bond_providers = db.Column(db.String(4096), nullable=True)
    bond = db.Column(db.BigInteger, nullable=True)
    current_award = db.Column(db.BigInteger, nullable=True)
    slash_points = db.Column(db.Integer, nullable=True)
    forced_to_leave = db.Column(db.Boolean, nullable=True)
    requested_to_leave = db.Column(db.Boolean, nullable=True)
    jail = db.Column(db.String(1024), nullable=True)
    bond_address = db.Column(db.String(255), nullable=True)
    observe_chains = db.Column(db.String(4096), nullable=True)
    preflight_status = db.Column(db.String(1024), nullable=True)
    status = db.Column(db.String(255), nullable=True)
    status_since = db.Column(db.Integer, nullable=True)
    version = db.Column(db.String(63), nullable=True)
    ip_address = db.Column(db.String(63), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    isp = db.Column(db.String(255), nullable=True)
    rpc = db.Column(db.String(1023), nullable=True)
    bifrost = db.Column(db.String(63), nullable=True)
    bondProvidersString = db.Column(db.String(1024), nullable=True)
    country = db.Column(db.String(255), nullable=True)
    country_code = db.Column(db.String(255), nullable=True)
    is_jailed = db.Column(db.Integer, default=0)

    def to_dict(self):
        """Convert the model instance to a dictionary."""
        return {
            "node_address": self.node_address,
            "active_block_height": self.active_block_height,
            "bond_providers": self.bond_providers,
            "bond": self.bond,
            "current_award": self.current_award,
            "slash_points": self.slash_points,
            "forced_to_leave": self.forced_to_leave,
            "requested_to_leave": self.requested_to_leave,
            "jail": self.jail,
            "bond_address": self.bond_address,
            "observe_chains": self.observe_chains,
            "preflight_status": self.preflight_status,
            "status": self.status,
            "status_since": self.status_since,
            "version": self.version,
            "ip_address": self.ip_address,
            "location": self.location,
            "isp": self.isp,
            "rpc": self.rpc,
            "bifrost": self.bifrost,
            "bondProvidersString": self.bondProvidersString,
            "country": self.country,
            "country_code": self.country_code,
            "is_jailed": self.is_jailed
        }

    def to_json(self):
        """Convert the model instance to a JSON string."""
        import json
        return json.dumps(self.to_dict())