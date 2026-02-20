import json
import requests
from datetime import datetime
from flask import Flask
from DB import db
from config import config
from API.mimir.models import MimirCache


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


def sync_mimir_scheduled(app: Flask):
    """APScheduler entry-point — provides its own app context."""
    with app.app_context():
        try:
            _sync_mimir()
        except Exception as e:
            db.session.rollback()
            print(f'[mimir] Sync failed: {e}')
