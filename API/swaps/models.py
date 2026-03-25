from DB import db
import json


class StreamingSwapCache(db.Model):
    """Single-row cache of live in-progress streaming swaps from THORNode."""
    __tablename__ = 'streaming_swap_cache'

    id         = db.Column(db.Integer,  primary_key=True)
    count      = db.Column(db.Integer,  nullable=True)
    data       = db.Column(db.Text,     nullable=True)   # JSON array
    updated_at = db.Column(db.DateTime, nullable=True)

    def swap_list(self):
        return json.loads(self.data) if self.data else []


class SwapHistory(db.Model):
    """Individual completed swaps (streaming + regular) from Midgard."""
    __tablename__ = 'swap_history'

    id                  = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    tx_id               = db.Column(db.String(255), unique=True, index=True, nullable=False)
    swap_type           = db.Column(db.String(50),  index=True)         # 'streaming' | 'regular'
    source_asset        = db.Column(db.String(255))
    target_asset        = db.Column(db.String(255))
    input_amount        = db.Column(db.BigInteger)                       # base units (1e8)
    output_amount       = db.Column(db.BigInteger)
    usd_value           = db.Column(db.Float,       index=True)
    affiliate_fee       = db.Column(db.String(50))
    swap_slip           = db.Column(db.String(50))                       # basis points
    liquidity_fee       = db.Column(db.BigInteger)
    streaming_count     = db.Column(db.Integer,     nullable=True)       # sub-swaps executed
    streaming_quantity  = db.Column(db.Integer,     nullable=True)       # sub-swaps planned
    streaming_interval  = db.Column(db.Integer,     nullable=True)       # blocks between subs
    block_height        = db.Column(db.BigInteger)
    block_timestamp     = db.Column(db.DateTime)
    sender_address      = db.Column(db.String(255))
    dest_address        = db.Column(db.String(255))
    pools               = db.Column(db.Text,        nullable=True)       # JSON array of pools
    data                = db.Column(db.Text,        nullable=True)       # full Midgard action JSON
    created_at          = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'tx_id':               self.tx_id,
            'swap_type':           self.swap_type,
            'source_asset':        self.source_asset,
            'target_asset':        self.target_asset,
            'input_amount':        self.input_amount,
            'output_amount':       self.output_amount,
            'usd_value':           self.usd_value,
            'affiliate_fee':       self.affiliate_fee,
            'swap_slip':           self.swap_slip,
            'liquidity_fee':       self.liquidity_fee,
            'streaming_count':     self.streaming_count,
            'streaming_quantity':  self.streaming_quantity,
            'streaming_interval':  self.streaming_interval,
            'block_height':        self.block_height,
            'block_timestamp':     self.block_timestamp.isoformat() if self.block_timestamp else None,
            'sender_address':      self.sender_address,
            'dest_address':        self.dest_address,
            'pools':               json.loads(self.pools) if self.pools else [],
        }
