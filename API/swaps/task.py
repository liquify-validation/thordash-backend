import json
import re
import requests
from datetime import datetime
from flask import Flask
from DB import db
from config import config
from API.swaps.models import StreamingSwapCache, SwapHistory
from API.pools.models import PoolCache


BLOCK_TIME_SECS = 6.0   # average THORChain block time


def _parse_streaming_memo(memo):
    """Extract interval and quantity from a THORChain streaming swap memo.
    Memo format: =:ASSET:ADDR:LIMIT/INTERVAL/QUANTITY  (or swap: prefix)
    """
    interval, quantity = None, None
    if not memo:
        return interval, quantity
    parts = memo.split(':')
    if len(parts) >= 4:
        limit_part = parts[3]
        segs = limit_part.split('/')
        if len(segs) >= 3:
            try:
                interval = int(segs[1])
            except (ValueError, IndexError):
                pass
            try:
                quantity = int(segs[2])
            except (ValueError, IndexError):
                pass
    return interval, quantity


def _estimate_single_swap_slip(source_asset, input_amount_base):
    """Estimate what slippage would be for a single (non-streaming) swap.
    Uses the THORChain slip formula: slip = x / (x + X)
    where x = input amount and X = pool depth on the input side.
    Returns slip as basis points, or None if we can't calculate.
    """
    if not source_asset or not input_amount_base:
        return None
    pool = PoolCache.query.filter_by(asset=source_asset).first()
    if not pool:
        return None
    # If source is RUNE, use rune_depth; otherwise use asset_depth
    if 'RUNE' in source_asset.upper() or source_asset.upper().startswith('THOR.'):
        depth = pool.rune_depth or 0
    else:
        depth = pool.asset_depth or 0
    if depth == 0:
        return None
    x = float(input_amount_base)
    X = float(depth)
    slip = x / (x + X)
    return round(slip * 10000, 2)  # basis points


def _compute_savings(swap_dict):
    """Add estimated savings fields to a swap dictionary."""
    if swap_dict.get('swap_type') != 'streaming':
        swap_dict['time_seconds'] = None
        swap_dict['estimated_single_slip_bps'] = None
        swap_dict['slip_saved_bps'] = None
        swap_dict['slip_saved_percent'] = None
        return swap_dict

    count = swap_dict.get('streaming_count') or 0
    interval = swap_dict.get('streaming_interval') or 1
    actual_slip = float(swap_dict.get('swap_slip') or 0)

    # Time the streaming swap took
    time_secs = count * interval * BLOCK_TIME_SECS
    swap_dict['time_seconds'] = round(time_secs)

    # Estimated single-swap slippage
    est_slip = _estimate_single_swap_slip(
        swap_dict.get('source_asset'),
        swap_dict.get('input_amount')
    )
    swap_dict['estimated_single_slip_bps'] = est_slip

    if est_slip is not None and est_slip > 0:
        saved = est_slip - actual_slip
        swap_dict['slip_saved_bps'] = round(saved, 2)
        swap_dict['slip_saved_percent'] = round((saved / est_slip) * 100, 1) if est_slip > 0 else 0
    else:
        swap_dict['slip_saved_bps'] = None
        swap_dict['slip_saved_percent'] = None

    return swap_dict


# ─── Sync live streaming swaps from THORNode ─────────────────────────

def _sync_streaming():
    """Fetch in-progress streaming swaps from THORNode."""
    now = datetime.utcnow()
    resp = requests.get(
        f'{config.Config.THORNODE_URL}/thorchain/swaps/streaming',
        timeout=10,
    )
    if resp.status_code != 200:
        print(f'[swaps] Failed to fetch streaming swaps (HTTP {resp.status_code})')
        return

    swaps = resp.json()

    row = StreamingSwapCache.query.filter_by(id=1).first()
    if row is None:
        row = StreamingSwapCache(id=1)
        db.session.add(row)

    row.count      = len(swaps) if isinstance(swaps, list) else 0
    row.data       = json.dumps(swaps)
    row.updated_at = now
    db.session.commit()
    print(f'[swaps] Synced {row.count} live streaming swaps')


# ─── Sync completed swaps from Midgard ───────────────────────────────

def _sync_swap_history():
    """Fetch recent completed swaps from Midgard and store new ones."""
    now = datetime.utcnow()

    resp = requests.get(
        f'{config.Config.MIDGARD_URL}/v2/actions?type=swap&limit=50',
        timeout=15,
    )
    if resp.status_code != 200:
        print(f'[swaps] Failed to fetch swap history (HTTP {resp.status_code})')
        return

    body = resp.json()
    actions = body.get('actions', [])
    new_count = 0

    for action in actions:
        if action.get('status') != 'success':
            continue

        in_tx = action.get('in', [{}])[0] if action.get('in') else {}
        out_tx = action.get('out', [{}])[0] if action.get('out') else {}
        meta = action.get('metadata', {}).get('swap', {})

        tx_id = in_tx.get('txID', '')
        if not tx_id:
            continue

        # Skip if already stored
        if SwapHistory.query.filter_by(tx_id=tx_id).first():
            continue

        in_coins = in_tx.get('coins', [{}])[0] if in_tx.get('coins') else {}
        out_coins = out_tx.get('coins', [{}])[0] if out_tx.get('coins') else {}

        source_asset = in_coins.get('asset', '')
        target_asset = out_coins.get('asset', '')
        input_amount = int(in_coins.get('amount', 0))
        output_amount = int(out_coins.get('amount', 0))

        is_streaming = meta.get('isStreamingSwap', False)
        memo = meta.get('memo', '')

        # Parse streaming params from memo
        s_interval, s_quantity = _parse_streaming_memo(memo)

        # Estimate USD value from Midgard price data
        in_price_usd = float(meta.get('inPriceUSD', 0) or 0)
        usd_value = (input_amount / 1e8) * in_price_usd if in_price_usd else 0

        # Timestamp from Midgard date field (nanoseconds since epoch)
        ts = None
        date_str = action.get('date', '')
        if date_str:
            try:
                ts = datetime.utcfromtimestamp(int(date_str) / 1e9)
            except (ValueError, OSError):
                pass

        row = SwapHistory(
            tx_id               = tx_id,
            swap_type           = 'streaming' if is_streaming else 'regular',
            source_asset        = source_asset,
            target_asset        = target_asset,
            input_amount        = input_amount,
            output_amount       = output_amount,
            usd_value           = round(usd_value, 2),
            affiliate_fee       = meta.get('affiliateFee', '0'),
            swap_slip           = meta.get('swapSlip', '0'),
            liquidity_fee       = int(meta.get('liquidityFee', 0) or 0),
            streaming_count     = s_quantity if is_streaming else None,  # completed = planned when done
            streaming_quantity  = s_quantity if is_streaming else None,
            streaming_interval  = s_interval if is_streaming else None,
            block_height        = int(action.get('height', 0)),
            block_timestamp     = ts,
            sender_address      = in_tx.get('address', ''),
            dest_address        = out_tx.get('address', ''),
            pools               = json.dumps(action.get('pools', [])),
            data                = json.dumps(action),
            created_at          = now,
        )
        db.session.add(row)
        new_count += 1

    if new_count > 0:
        db.session.commit()
    print(f'[swaps] Stored {new_count} new completed swaps')


# ─── APScheduler entry points ────────────────────────────────────────

def sync_streaming_scheduled(app: Flask):
    with app.app_context():
        try:
            _sync_streaming()
        except Exception as e:
            db.session.rollback()
            print(f'[swaps] Streaming sync failed: {e}')


def sync_swap_history_scheduled(app: Flask):
    with app.app_context():
        try:
            _sync_swap_history()
        except Exception as e:
            db.session.rollback()
            print(f'[swaps] History sync failed: {e}')
