import json
from datetime import datetime, timedelta
from flask import jsonify, request
from flask_smorest import Blueprint
from sqlalchemy import func
from API.swaps.models import StreamingSwapCache, SwapHistory
from API.swaps.task import _sync_streaming, _sync_swap_history, _compute_savings

blp = Blueprint("swaps", __name__, description="THORChain Swap Tracker API")

_NO_DATA = {"error": "No swap data available yet. POST /swaps/sync to populate."}


@blp.route('/sync', methods=['POST'])
def sync():
    """Manually trigger a swap data refresh
    ---
    tags:
      - Swaps
    responses:
      200:
        description: Sync completed successfully
    """
    _sync_streaming()
    _sync_swap_history()
    return jsonify({"message": "Swap data synced successfully"})


@blp.route('/streaming', methods=['GET'])
def get_streaming():
    """Returns live in-progress streaming swaps
    ---
    tags:
      - Swaps
    responses:
      200:
        description: Array of live streaming swaps from THORNode
      503:
        description: Cache not yet populated
    """
    row = StreamingSwapCache.query.filter_by(id=1).first()
    if row is None:
        return jsonify(_NO_DATA), 503
    return jsonify({
        'count': row.count,
        'swaps': row.swap_list(),
        'updated_at': row.updated_at.isoformat() if row.updated_at else None,
    })


@blp.route('/history', methods=['GET'])
def get_history():
    """Returns completed swap history with optional filters
    ---
    tags:
      - Swaps
    parameters:
      - name: type
        in: query
        type: string
        description: Filter by swap type (streaming, regular)
      - name: limit
        in: query
        type: integer
        description: Max results (default 50, max 200)
      - name: sort
        in: query
        type: string
        description: Sort field (usd_value, block_timestamp). Default usd_value desc.
      - name: asset
        in: query
        type: string
        description: Filter by source or target asset (partial match)
    responses:
      200:
        description: Array of completed swaps
    """
    swap_type = request.args.get('type')
    limit = min(int(request.args.get('limit', 50)), 200)
    sort = request.args.get('sort', 'usd_value')
    asset = request.args.get('asset')

    query = SwapHistory.query

    if swap_type:
        query = query.filter(SwapHistory.swap_type == swap_type)
    if asset:
        like = f'%{asset}%'
        query = query.filter(
            (SwapHistory.source_asset.like(like)) | (SwapHistory.target_asset.like(like))
        )

    if sort == 'block_timestamp':
        query = query.order_by(SwapHistory.block_timestamp.desc())
    else:
        query = query.order_by(SwapHistory.usd_value.desc())

    rows = query.limit(limit).all()
    swaps = [_compute_savings(r.to_dict()) for r in rows]
    return jsonify(swaps)


@blp.route('/recent', methods=['GET'])
def get_recent():
    """Returns swaps from the last 24 hours, most recent first
    ---
    tags:
      - Swaps
    parameters:
      - name: type
        in: query
        type: string
        description: Filter by swap type (streaming, regular)
    responses:
      200:
        description: Array of recent swaps
    """
    cutoff = datetime.utcnow() - timedelta(hours=24)
    swap_type = request.args.get('type')

    query = SwapHistory.query.filter(SwapHistory.block_timestamp >= cutoff)
    if swap_type:
        query = query.filter(SwapHistory.swap_type == swap_type)

    rows = query.order_by(SwapHistory.block_timestamp.desc()).all()
    swaps = [_compute_savings(r.to_dict()) for r in rows]
    return jsonify(swaps)


@blp.route('/stats', methods=['GET'])
def get_stats():
    """Returns aggregate swap statistics
    ---
    tags:
      - Swaps
    responses:
      200:
        description: Swap statistics (24h count, volume, all-time stats)
    """
    now = datetime.utcnow()
    cutoff_24h = now - timedelta(hours=24)

    # 24h stats
    stats_24h = SwapHistory.query.filter(
        SwapHistory.block_timestamp >= cutoff_24h
    ).with_entities(
        func.count(SwapHistory.id),
        func.coalesce(func.sum(SwapHistory.usd_value), 0),
    ).first()

    # 24h streaming-only
    streaming_24h = SwapHistory.query.filter(
        SwapHistory.block_timestamp >= cutoff_24h,
        SwapHistory.swap_type == 'streaming',
    ).with_entities(
        func.count(SwapHistory.id),
        func.coalesce(func.sum(SwapHistory.usd_value), 0),
    ).first()

    # All-time stats
    all_time = SwapHistory.query.with_entities(
        func.count(SwapHistory.id),
        func.coalesce(func.sum(SwapHistory.usd_value), 0),
        func.max(SwapHistory.usd_value),
    ).first()

    # Live streaming count
    live = StreamingSwapCache.query.filter_by(id=1).first()

    # Total estimated time saved (sum of time_seconds for streaming swaps)
    streaming_rows = SwapHistory.query.filter(
        SwapHistory.swap_type == 'streaming',
        SwapHistory.streaming_count.isnot(None),
        SwapHistory.streaming_interval.isnot(None),
    ).all()
    total_time_secs = sum(
        (r.streaming_count or 0) * (r.streaming_interval or 1) * 6
        for r in streaming_rows
    )

    # Average slip saved for streaming swaps
    streaming_with_savings = [
        _compute_savings(r.to_dict()) for r in streaming_rows
    ]
    slip_savings = [
        s['slip_saved_percent'] for s in streaming_with_savings
        if s.get('slip_saved_percent') is not None and s['slip_saved_percent'] > 0
    ]
    avg_slip_saved = round(sum(slip_savings) / len(slip_savings), 1) if slip_savings else 0

    return jsonify({
        'count_24h':           stats_24h[0],
        'volume_24h_usd':     round(stats_24h[1], 2),
        'streaming_count_24h': streaming_24h[0],
        'streaming_volume_24h_usd': round(streaming_24h[1], 2),
        'total_swaps':         all_time[0],
        'total_volume_usd':    round(all_time[1], 2),
        'largest_swap_usd':    round(all_time[2], 2) if all_time[2] else 0,
        'live_streaming':      live.count if live else 0,
        'total_time_saved_secs': total_time_secs,
        'avg_fee_saved_pct':   avg_slip_saved,
    })
