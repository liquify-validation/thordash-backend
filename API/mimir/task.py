import json
import requests
from datetime import datetime
from flask import Flask
from DB import db
from config import config
from API.mimir.models import MimirCache, MimirVotesCache


def _sync_mimir():
    """Core mimir sync logic. Must be called within an active app context."""
    response = requests.get(f'{config.Config.THORNODE_URL}/thorchain/mimir', timeout=10)
    if response.status_code != 200:
        print(f'[mimir] Failed to fetch mimir data (HTTP {response.status_code})')
        return

    now = datetime.utcnow()
    row = MimirCache.query.filter_by(id=1).first()
    if row is None:
        row = MimirCache(id=1)
        db.session.add(row)

    row.data       = json.dumps(response.json())
    row.updated_at = now
    db.session.commit()
    print(f'[mimir] Synced {len(response.json())} parameters')


def _sync_mimir_votes():
    """Fetch per-node mimir votes from THORNode and cache them."""
    response = requests.get(f'{config.Config.THORNODE_URL}/thorchain/mimir/nodes_all', timeout=10)
    if response.status_code != 200:
        print(f'[mimir-votes] Failed to fetch node votes (HTTP {response.status_code})')
        return

    raw_votes = response.json()  # list of {key, value, signer}

    # Build a structured dict: { node_address: { mimir_key: value, ... } }
    by_node = {}
    # Also track per-key vote counts: { mimir_key: { value: count } }
    by_key = {}
    for vote in raw_votes:
        signer = vote.get('signer', '')
        key    = vote.get('key', '')
        value  = vote.get('value')

        # Per-node grouping
        if signer not in by_node:
            by_node[signer] = {}
        by_node[signer][key] = value

        # Per-key consensus tracking
        if key not in by_key:
            by_key[key] = {}
        str_val = str(value)
        by_key[key][str_val] = by_key[key].get(str_val, 0) + 1

    result = {
        "raw": raw_votes,
        "byNode": by_node,
        "byKey": by_key,
        "totalVotes": len(raw_votes),
        "totalNodes": len(by_node),
    }

    now = datetime.utcnow()
    row = MimirVotesCache.query.filter_by(id=1).first()
    if row is None:
        row = MimirVotesCache(id=1)
        db.session.add(row)

    row.data       = json.dumps(result)
    row.updated_at = now
    db.session.commit()
    print(f'[mimir-votes] Synced {len(raw_votes)} votes from {len(by_node)} nodes')


def sync_mimir_scheduled(app: Flask):
    """APScheduler entry-point — provides its own app context."""
    with app.app_context():
        try:
            _sync_mimir()
        except Exception as e:
            db.session.rollback()
            print(f'[mimir] Sync failed: {e}')


def sync_mimir_votes_scheduled(app: Flask):
    """APScheduler entry-point for node vote sync."""
    with app.app_context():
        try:
            _sync_mimir_votes()
        except Exception as e:
            db.session.rollback()
            print(f'[mimir-votes] Sync failed: {e}')
