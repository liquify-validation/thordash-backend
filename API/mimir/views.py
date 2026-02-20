from flask import jsonify
from flask_smorest import Blueprint
from API.mimir.models import MimirCache
from API.mimir.task import _sync_mimir

blp = Blueprint("mimir", __name__, description="THORChain Mimir (network governance parameters) API")

_NO_DATA = {"error": "No mimir data available yet. POST /mimir/sync to populate."}


@blp.route('/sync', methods=['POST'])
def sync():
    """Manually trigger a mimir data refresh from THORNode
    ---
    tags:
      - Mimir
    responses:
      200:
        description: Sync completed successfully
    """
    _sync_mimir()
    return jsonify({"message": "Mimir data synced successfully"})


@blp.route('/', methods=['GET'])
def get_mimir():
    """Returns all current mimir on-chain governance parameters from the local cache
    ---
    tags:
      - Mimir
    responses:
      200:
        description: All mimir key-value pairs (e.g. CHURNINTERVAL, MAXNODECOUNT, slash limits)
      503:
        description: Cache not yet populated — POST /mimir/sync first
    """
    row = MimirCache.query.filter_by(id=1).first()
    if row is None:
        return jsonify(_NO_DATA), 503
    return jsonify(row.to_dict())


@blp.route('/<key>', methods=['GET'])
def get_mimir_key(key):
    """Returns the value for a specific mimir key from the local cache
    ---
    tags:
      - Mimir
    parameters:
      - name: key
        in: path
        required: true
        type: string
        description: Mimir key name (case-insensitive, e.g. CHURNINTERVAL, MAXNODECOUNT)
    responses:
      200:
        description: Value for the requested mimir key
      404:
        description: Key not found in mimir
      503:
        description: Cache not yet populated
    """
    row = MimirCache.query.filter_by(id=1).first()
    if row is None:
        return jsonify(_NO_DATA), 503

    data      = row.to_dict()
    upper_key = key.upper()

    if upper_key not in data:
        return jsonify({"error": f"Mimir key '{key}' not found"}), 404

    return jsonify({upper_key: data[upper_key]})
