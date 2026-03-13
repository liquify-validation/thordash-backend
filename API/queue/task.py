import json
import requests
from datetime import datetime
from flask import Flask
from DB import db
from config import config
from API.queue.models import QueueCache


def _sync_queue():
    """Core queue sync logic. Must be called within an active app context."""
    now = datetime.utcnow()

    summary_resp   = requests.get(f'{config.Config.THORNODE_URL}/thorchain/queue',           timeout=10)
    outbound_resp  = requests.get(f'{config.Config.THORNODE_URL}/thorchain/queue/outbound',  timeout=10)
    scheduled_resp = requests.get(f'{config.Config.THORNODE_URL}/thorchain/queue/scheduled', timeout=10)

    if summary_resp.status_code != 200:
        print(f'[queue] Failed to fetch queue summary (HTTP {summary_resp.status_code})')
        return

    summary = summary_resp.json()

    row = QueueCache.query.filter_by(id=1).first()
    if row is None:
        row = QueueCache(id=1)
        db.session.add(row)

    row.outbound_count  = summary.get('outbound',  0)
    row.scheduled_count = summary.get('scheduled', 0)
    row.swap_count      = summary.get('swap',      0)
    row.outbound_data   = json.dumps(outbound_resp.json()  if outbound_resp.status_code  == 200 else [])
    row.scheduled_data  = json.dumps(scheduled_resp.json() if scheduled_resp.status_code == 200 else [])
    row.updated_at      = now

    db.session.commit()
    print(f'[queue] Synced — outbound: {row.outbound_count}, scheduled: {row.scheduled_count}, swap: {row.swap_count}')


def sync_queue_scheduled(app: Flask):
    """APScheduler entry-point — provides its own app context."""
    with app.app_context():
        try:
            _sync_queue()
        except Exception as e:
            db.session.rollback()
            print(f'[queue] Sync failed: {e}')
