import json
import requests
from datetime import datetime
from flask import Flask
from DB import db
from config import config
from API.pools.models import PoolCache, PoolStatsCache


def _sync_pools():
    """Core pool sync logic. Must be called within an active app context."""
    now = datetime.utcnow()

    pools_resp = requests.get(f'{config.Config.MIDGARD_URL}/v2/pools', timeout=10)
    stats_resp = requests.get(f'{config.Config.MIDGARD_URL}/v2/stats',  timeout=10)

    # Sync pool list
    if pools_resp.status_code == 200:
        pools = pools_resp.json()
        # Track which assets came back from the API so we can mark missing ones Suspended
        api_assets = set()

        for pool in pools:
            asset = pool.get('asset')
            if not asset:
                continue
            api_assets.add(asset)

            row = PoolCache.query.filter_by(asset=asset).first()
            if row is None:
                row = PoolCache(asset=asset)
                db.session.add(row)

            row.status          = pool.get('status')
            row.asset_depth     = int(pool.get('assetDepth',   0) or 0)
            row.rune_depth      = int(pool.get('runeDepth',    0) or 0)
            row.pool_apy        = float(pool.get('poolAPY',   0.0) or 0.0)
            row.asset_price_usd = str(pool.get('assetPriceUSD', ''))
            row.volume_24h      = int(pool.get('volume24h',   0) or 0)
            row.data            = json.dumps(pool)
            row.updated_at      = now

        db.session.commit()
        print(f'[pools] Synced {len(pools)} pools')
    else:
        print(f'[pools] Failed to fetch pools (HTTP {pools_resp.status_code})')

    # Sync global stats
    if stats_resp.status_code == 200:
        row = PoolStatsCache.query.filter_by(id=1).first()
        if row is None:
            row = PoolStatsCache(id=1)
            db.session.add(row)
        row.data       = json.dumps(stats_resp.json())
        row.updated_at = now
        db.session.commit()
        print('[pools] Synced global stats')
    else:
        print(f'[pools] Failed to fetch stats (HTTP {stats_resp.status_code})')


def sync_pools_scheduled(app: Flask):
    """APScheduler entry-point — provides its own app context."""
    with app.app_context():
        try:
            _sync_pools()
        except Exception as e:
            db.session.rollback()
            print(f'[pools] Sync failed: {e}')
