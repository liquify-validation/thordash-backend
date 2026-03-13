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

    payload = response.json()
    print(f'[mimir-votes] Response type: {type(payload).__name__}')
    if isinstance(payload, dict):
        print(f'[mimir-votes] Top-level keys ({len(payload)}): {list(payload.keys())[:5]}')
        # Show first key's value type
        for k, v in list(payload.items())[:1]:
            print(f'[mimir-votes] Sample key "{k}" -> type={type(v).__name__}, value={str(v)[:200]}')
    elif isinstance(payload, list):
        print(f'[mimir-votes] List length: {len(payload)}')
        if payload:
            print(f'[mimir-votes] First item: {payload[0]}')

    # THORNode can return either:
    #   - a list of {key, value, signer} objects, OR
    #   - a dict like { "MIMIRKEY": { "thor1...": 1, "thor2...": 1 }, ... }
    #   - a dict like { "mimirs": [...] } (wrapped format)
    raw_votes = []
    if isinstance(payload, list):
        raw_votes = payload
    elif isinstance(payload, dict):
        # Check if it's wrapped in a "mimirs" key
        if "mimirs" in payload and isinstance(payload["mimirs"], list):
            raw_votes = payload["mimirs"]
        else:
            # Dict format: { "MIMIRKEY": { "thor1...": 1, ... }, ... }
            for mimir_key, signers in payload.items():
                if isinstance(signers, dict):
                    for signer_addr, val in signers.items():
                        raw_votes.append({"key": mimir_key, "value": val, "signer": signer_addr})
                elif isinstance(signers, int):
                    # Single value, not per-node — skip or handle
                    pass
    else:
        print(f'[mimir-votes] Unexpected response type: {type(payload)}')
        return

    print(f'[mimir-votes] Parsed {len(raw_votes)} raw votes')

    # Build a structured dict: { node_address: { mimir_key: value, ... } }
    by_node = {}
    # Also track per-key vote counts: { mimir_key: { value: count } }
    by_key = {}
    for vote in raw_votes:
        if not isinstance(vote, dict):
            continue
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
