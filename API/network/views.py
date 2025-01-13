from flask import request, jsonify
import json
from flask_smorest import Blueprint, abort
from API.network.service import *

from config import config

blp = Blueprint("network", __name__, description="Network stats API")

@blp.route('/grabChurns', methods=['GET'])
def grab_churns():
    """Returns a list of past churns which are indexed by the API
       ---
       tags:
         - Network
       responses:
         200:
           description: List of churn heights indexed
       """
    response_API = requests.get(config.Config.MIDGARD_URL + '/v2/churns')
    data = json.loads(response_API.text)

    return jsonify(data)

@blp.route('/haltedChains', methods=['GET'])
def grab_halted():
    """Returns current chain status
           ---
           tags:
             - Network
           responses:
             200:
               description: List of churn heights indexed
           """
    halts = get_feild("halts")

    if halts:
        return jsonify({
            "halts": json.loads(halts)
        })
    else:
        return jsonify({"error": "No record found"}), 404

@blp.route('/getCurrentHeight', methods=['GET'])
def grab_halted():
    """Returns current indexed height
           ---
           tags:
             - Network
           responses:
             200:
               description: current indexed height
           """
    height = get_feild("maxHeight")

    if height:
        return str(height)
    else:
        return jsonify({"error": "No record found"}), 404

@blp.route('/getBlockTime', methods=['GET'])
def grab_halted():
    """Returns the average blocktime over the last 100 blocks
           ---
           tags:
             - Network
           responses:
             200:
               description: average block time across the last 100 blocks
           """
    blockTime = get_feild("secondsPerBlock")

    if blockTime:
        return str(blockTime)
    else:
        return jsonify({"error": "No record found"}), 404

@blp.route('/getMaxEffectiveStake', methods=['GET'])
def grab_max_effective_stake():
    """Returns the max effective stake
           ---
           tags:
             - Network
           responses:
             200:
               description: return the current max effective stake
           """
    maxEffectiveStake = get_feild("maxEffectiveStake")

    if maxEffectiveStake:
        return str(maxEffectiveStake)
    else:
        return jsonify({"error": "No record found"}), 404

@blp.route('/getCoinGeckoData', methods=['GET'])
def grab_max_effective_stake():
    """Returns the current coingecko data for Rune
           ---
           tags:
             - Network
           responses:
             200:
               description: return the current coingecko data for Rune
           """
    coingecko = get_feild("coingecko")

    if coingecko:
        return str(coingecko)
    else:
        return jsonify({"error": "No record found"}), 404

@blp.route('/dumpNetworkInfo', methods=['GET'])
def grab_all_network_info():
    """Returns the current network info
           ---
           tags:
             - Network
           responses:
             200:
               description: return the current network info
           """
    network_info = get_network_info()

    if network_info:
        return json.loads(network_info)
    else:
        return jsonify({"error": "No record found"}), 404