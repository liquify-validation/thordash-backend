from flask import jsonify
from flask_smorest import Blueprint
from API.vaults.models import VaultCache
from API.vaults.task import _sync_vaults

blp = Blueprint("vaults", __name__, description="THORChain Vault API")

_NO_DATA = {"error": "No vault data available yet. POST /vaults/sync to populate."}


@blp.route('/sync', methods=['POST'])
def sync():
    """Manually trigger a vault data refresh from THORNode
    ---
    tags:
      - Vaults
    responses:
      200:
        description: Sync completed successfully
    """
    _sync_vaults()
    return jsonify({"message": "Vault data synced successfully"})


@blp.route('/asgard', methods=['GET'])
def get_asgard_vaults():
    """Returns all asgard vaults from the local cache
    ---
    tags:
      - Vaults
    responses:
      200:
        description: List of asgard vaults with members and coin balances
      503:
        description: Cache not yet populated — POST /vaults/sync first
    """
    rows = VaultCache.query.filter_by(vault_type='asgard').all()
    if not rows:
        return jsonify(_NO_DATA), 503
    return jsonify([r.to_dict() for r in rows])


@blp.route('/asgard/active', methods=['GET'])
def get_active_asgard_vaults():
    """Returns only active asgard vaults from the local cache
    ---
    tags:
      - Vaults
    responses:
      200:
        description: List of active asgard vaults
      503:
        description: Cache not yet populated
    """
    rows = VaultCache.query.filter_by(vault_type='asgard', status='ActiveVault').all()
    if not rows:
        return jsonify(_NO_DATA), 503
    return jsonify([r.to_dict() for r in rows])


@blp.route('/pending', methods=['GET'])
def get_pending_vaults():
    """Returns retiring or inactive asgard vaults from the local cache
    ---
    tags:
      - Vaults
    responses:
      200:
        description: List of non-active asgard vaults
      503:
        description: Cache not yet populated
    """
    rows = (
        VaultCache.query
        .filter_by(vault_type='asgard')
        .filter(VaultCache.status != 'ActiveVault')
        .all()
    )
    if not rows:
        return jsonify(_NO_DATA), 503
    return jsonify([r.to_dict() for r in rows])


@blp.route('/yggdrasil', methods=['GET'])
def get_yggdrasil_vaults():
    """Returns all yggdrasil vaults (one per active node) from the local cache
    ---
    tags:
      - Vaults
    responses:
      200:
        description: List of yggdrasil vaults with per-node coin balances
      503:
        description: Cache not yet populated
    """
    rows = VaultCache.query.filter_by(vault_type='yggdrasil').all()
    if not rows:
        return jsonify(_NO_DATA), 503
    return jsonify([r.to_dict() for r in rows])


@blp.route('/yggdrasil/<node_address>', methods=['GET'])
def get_yggdrasil_vault_for_node(node_address):
    """Returns the yggdrasil vault for a specific node address from the local cache
    ---
    tags:
      - Vaults
    parameters:
      - name: node_address
        in: path
        required: true
        type: string
        description: THORChain node address (thor1...)
    responses:
      200:
        description: Yggdrasil vault for the specified node
      404:
        description: No vault found for that node address
      503:
        description: Cache not yet populated
    """
    row = VaultCache.query.filter_by(vault_type='yggdrasil', node_address=node_address).first()
    if row is None:
        if VaultCache.query.filter_by(vault_type='yggdrasil').count() == 0:
            return jsonify(_NO_DATA), 503
        return jsonify({"error": f"No yggdrasil vault found for node '{node_address}'"}), 404
    return jsonify(row.to_dict())


@blp.route('/totalLocked', methods=['GET'])
def get_total_locked():
    """Returns total value locked across all cached vaults, summed by asset
    ---
    tags:
      - Vaults
    responses:
      200:
        description: Dict mapping asset to total amount locked (1e-8 units)
      503:
        description: Cache not yet populated
    """
    rows = VaultCache.query.all()
    if not rows:
        return jsonify(_NO_DATA), 503

    totals = {}
    for row in rows:
        for coin in row.to_dict()['coins']:
            asset  = coin.get('asset')
            amount = int(coin.get('amount', 0))
            totals[asset] = totals.get(asset, 0) + amount

    return jsonify(totals)
