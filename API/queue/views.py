from flask import jsonify
from flask_smorest import Blueprint
from API.queue.models import QueueCache
from API.queue.task import _sync_queue

blp = Blueprint("queue", __name__, description="THORChain Outbound Queue API")

_NO_DATA = {"error": "No queue data available yet. POST /queue/sync to populate."}


@blp.route('/sync', methods=['POST'])
def sync():
    """Manually trigger a queue data refresh from THORNode
    ---
    tags:
      - Queue
    responses:
      200:
        description: Sync completed successfully
    """
    _sync_queue()
    return jsonify({"message": "Queue data synced successfully"})


@blp.route('/', methods=['GET'])
def get_queue():
    """Returns the outbound queue summary from the local cache
    ---
    tags:
      - Queue
    responses:
      200:
        description: Queue counts for outbound, scheduled and swap. High outbound count indicates congestion.
      503:
        description: Cache not yet populated — POST /queue/sync first
    """
    row = QueueCache.query.filter_by(id=1).first()
    if row is None:
        return jsonify(_NO_DATA), 503
    return jsonify(row.summary())


@blp.route('/outbound', methods=['GET'])
def get_outbound_queue():
    """Returns the list of pending outbound transactions from the local cache
    ---
    tags:
      - Queue
    responses:
      200:
        description: Array of pending outbound transactions
      503:
        description: Cache not yet populated
    """
    row = QueueCache.query.filter_by(id=1).first()
    if row is None:
        return jsonify(_NO_DATA), 503
    return jsonify(row.outbound_list())


@blp.route('/scheduled', methods=['GET'])
def get_scheduled_queue():
    """Returns transactions scheduled for future outbound processing from the local cache
    ---
    tags:
      - Queue
    responses:
      200:
        description: Array of scheduled outbound transactions
      503:
        description: Cache not yet populated
    """
    row = QueueCache.query.filter_by(id=1).first()
    if row is None:
        return jsonify(_NO_DATA), 503
    return jsonify(row.scheduled_list())
