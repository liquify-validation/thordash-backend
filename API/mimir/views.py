from flask import jsonify
from flask_smorest import Blueprint
from API.mimir.models import MimirCache, MimirVotesCache
from API.mimir.task import _sync_mimir, _sync_mimir_votes

blp = Blueprint("mimir", __name__, description="THORChain Mimir (network governance parameters) API")

_NO_DATA = {"error": "No mimir data available yet. POST /mimir/sync to populate."}
_NO_VOTES = {"error": "No mimir vote data available yet. POST /mimir/votes/sync to populate."}


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


# ── Mimir Node Votes ──────────────────────────────────────────────

@blp.route('/votes/sync', methods=['POST'])
def sync_votes():
    """Manually trigger a mimir node votes refresh from THORNode
    ---
    tags:
      - Mimir Votes
    responses:
      200:
        description: Sync completed successfully
    """
    _sync_mimir_votes()
    return jsonify({"message": "Mimir vote data synced successfully"})


@blp.route('/votes', methods=['GET'])
def get_votes():
    """Returns all node mimir votes grouped by node and by key
    ---
    tags:
      - Mimir Votes
    responses:
      200:
        description: "Object with: byNode (node -> votes), byKey (key -> value counts), totalVotes, totalNodes"
      503:
        description: Cache not yet populated
    """
    row = MimirVotesCache.query.filter_by(id=1).first()
    if row is None:
        return jsonify(_NO_VOTES), 503
    return jsonify(row.to_dict())


@blp.route('/votes/node/<address>', methods=['GET'])
def get_votes_by_node(address):
    """Returns all mimir votes cast by a specific node
    ---
    tags:
      - Mimir Votes
    parameters:
      - name: address
        in: path
        required: true
        type: string
        description: Node address (e.g. thor1...)
    responses:
      200:
        description: "Object of { mimirKey: value } for this node"
      404:
        description: No votes found for this node
      503:
        description: Cache not yet populated
    """
    row = MimirVotesCache.query.filter_by(id=1).first()
    if row is None:
        return jsonify(_NO_VOTES), 503

    data = row.to_dict()
    by_node = data.get("byNode", {})

    if address not in by_node:
        return jsonify({"error": f"No votes found for node '{address}'"}), 404

    return jsonify({"address": address, "votes": by_node[address]})


@blp.route('/votes/key/<key>', methods=['GET'])
def get_votes_by_key(key):
    """Returns vote breakdown for a specific mimir key
    ---
    tags:
      - Mimir Votes
    parameters:
      - name: key
        in: path
        required: true
        type: string
        description: Mimir key name (case-insensitive)
    responses:
      200:
        description: "Object with vote value counts and list of voters"
      404:
        description: No votes found for this key
      503:
        description: Cache not yet populated
    """
    row = MimirVotesCache.query.filter_by(id=1).first()
    if row is None:
        return jsonify(_NO_VOTES), 503

    data = row.to_dict()
    by_key  = data.get("byKey", {})
    by_node = data.get("byNode", {})
    upper_key = key.upper()

    if upper_key not in by_key:
        return jsonify({"error": f"No votes found for mimir key '{key}'"}), 404

    # Build list of voters for this key
    voters = []
    for node_addr, node_votes in by_node.items():
        if upper_key in node_votes:
            voters.append({"address": node_addr, "value": node_votes[upper_key]})

    return jsonify({
        "key": upper_key,
        "valueCounts": by_key[upper_key],
        "voters": voters,
        "totalVoters": len(voters),
    })
