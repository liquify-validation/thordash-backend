from flask import jsonify, request
from flask_smorest import Blueprint
from API.pools.models import PoolCache, PoolStatsCache
from API.pools.task import _sync_pools

blp = Blueprint("pools", __name__, description="THORChain Liquidity Pools API")

_NO_DATA = {"error": "No pool data available yet. POST /pools/sync to populate."}


@blp.route('/sync', methods=['POST'])
def sync():
    """Manually trigger a pool data refresh from Midgard
    ---
    tags:
      - Pools
    responses:
      200:
        description: Sync completed successfully
    """
    _sync_pools()
    return jsonify({"message": "Pool data synced successfully"})


@blp.route('/', methods=['GET'])
def get_pools():
    """Returns all liquidity pools from the local cache
    ---
    tags:
      - Pools
    parameters:
      - name: status
        in: query
        required: false
        type: string
        description: Filter by pool status (Available, Staged, Suspended)
    responses:
      200:
        description: List of pools with depth, volume and APY data
      503:
        description: Cache not yet populated — POST /pools/sync first
    """
    status = request.args.get('status')
    query  = PoolCache.query
    if status:
        query = query.filter_by(status=status)

    rows = query.all()
    if not rows:
        return jsonify(_NO_DATA), 503
    return jsonify([r.to_dict() for r in rows])


@blp.route('/stats', methods=['GET'])
def get_stats():
    """Returns protocol-wide statistics from the local cache
    ---
    tags:
      - Pools
    responses:
      200:
        description: Global protocol statistics (swap volume, total users, liquidity)
      503:
        description: Cache not yet populated
    """
    row = PoolStatsCache.query.filter_by(id=1).first()
    if row is None:
        return jsonify(_NO_DATA), 503
    return jsonify(row.to_dict())


@blp.route('/<path:asset>', methods=['GET'])
def get_pool(asset):
    """Returns detail for a specific liquidity pool from the local cache
    ---
    tags:
      - Pools
    parameters:
      - name: asset
        in: path
        required: true
        type: string
        description: Asset identifier (e.g. BTC.BTC, ETH.ETH)
    responses:
      200:
        description: Pool detail including depth, APY, volume and price
      404:
        description: Pool not found in cache
      503:
        description: Cache not yet populated
    """
    row = PoolCache.query.filter_by(asset=asset).first()
    if row is None:
        if PoolCache.query.count() == 0:
            return jsonify(_NO_DATA), 503
        return jsonify({"error": f"Pool '{asset}' not found"}), 404
    return jsonify(row.to_dict())
