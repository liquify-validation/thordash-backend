from DB import db
import json


class VaultCache(db.Model):
    __tablename__ = 'vault_cache'

    pub_key      = db.Column(db.String(255), primary_key=True)
    vault_type   = db.Column(db.String(20),  nullable=False)   # 'asgard' | 'yggdrasil'
    status       = db.Column(db.String(50),  nullable=True)
    block_height = db.Column(db.BigInteger,  nullable=True)
    coins        = db.Column(db.Text,        nullable=True)    # JSON array
    membership   = db.Column(db.Text,        nullable=True)    # JSON array (asgard only)
    node_address = db.Column(db.String(255), nullable=True)    # populated for yggdrasil
    updated_at   = db.Column(db.DateTime,    nullable=True)

    def to_dict(self):
        return {
            'pub_key':      self.pub_key,
            'vault_type':   self.vault_type,
            'status':       self.status,
            'block_height': self.block_height,
            'coins':        json.loads(self.coins)      if self.coins      else [],
            'membership':   json.loads(self.membership) if self.membership else [],
            'node_address': self.node_address,
        }
