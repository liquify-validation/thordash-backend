import json
import requests
from datetime import datetime
from flask import Flask
from DB import db
from config import config
from API.vaults.models import VaultCache


def _sync_vaults():
    """Core vault sync logic. Must be called within an active app context."""
    now = datetime.utcnow()

    asgard_resp = requests.get(f'{config.Config.THORNODE_URL}/thorchain/vaults/asgard', timeout=10)

    if asgard_resp.status_code != 200:
        print(f'[vaults] Failed to fetch asgard vaults (HTTP {asgard_resp.status_code})')
        return

    asgard_vaults = asgard_resp.json()

    # Upsert asgard vaults
    for vault in asgard_vaults:
        row = VaultCache.query.filter_by(pub_key=vault['pub_key']).first()
        if row is None:
            row = VaultCache(pub_key=vault['pub_key'])
            db.session.add(row)
        row.vault_type   = 'asgard'
        row.status       = vault.get('status')
        row.block_height = vault.get('block_height')
        row.coins        = json.dumps(vault.get('coins', []))
        row.membership   = json.dumps(vault.get('membership', []))
        row.node_address = None
        row.updated_at   = now

    # Yggdrasil vaults were deprecated (TSS-only model) — sync if the endpoint is still available
    ygg_resp = requests.get(f'{config.Config.THORNODE_URL}/thorchain/vaults/yggdrasil', timeout=10)
    ygg_count = 0
    if ygg_resp.status_code == 200:
        ygg_vaults = ygg_resp.json()
        ygg_count  = len(ygg_vaults)

        # Build pub_key -> node_address map
        pub_key_to_addr = {}
        nodes_resp = requests.get(f'{config.Config.THORNODE_URL}/thorchain/nodes', timeout=10)
        if nodes_resp.status_code == 200:
            for node in nodes_resp.json():
                addr        = node.get('node_address')
                pub_key_set = node.get('pub_key_set', {})
                for key in (pub_key_set.get('secp256k1'), pub_key_set.get('ed25519')):
                    if key:
                        pub_key_to_addr[key] = addr

        # Replace yggdrasil rows wholesale — nodes churn in/out so stale rows must be removed
        VaultCache.query.filter_by(vault_type='yggdrasil').delete()
        for vault in ygg_vaults:
            pub_key = vault.get('pub_key')
            db.session.add(VaultCache(
                pub_key      = pub_key,
                vault_type   = 'yggdrasil',
                status       = vault.get('status'),
                block_height = vault.get('block_height'),
                coins        = json.dumps(vault.get('coins', [])),
                membership   = json.dumps([]),
                node_address = pub_key_to_addr.get(pub_key),
                updated_at   = now,
            ))

    db.session.commit()
    print(f'[vaults] Synced {len(asgard_vaults)} asgard + {ygg_count} yggdrasil vaults')


def sync_vaults_scheduled(app: Flask):
    """APScheduler entry-point — provides its own app context."""
    with app.app_context():
        try:
            _sync_vaults()
        except Exception as e:
            db.session.rollback()
            print(f'[vaults] Sync failed: {e}')
