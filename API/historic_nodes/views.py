import copy

from flask import request, jsonify
import json
from flask_smorest import Blueprint, abort
from API.network.service import *
from flask import request, jsonify
from API.historic_nodes.models import ThornodeMonitorHistoric
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func
from Common.common import convert_date_format
import time
from API.histroic_global.models import ThornodeMonitorGlobalHistoric
from API.histroic_global.views import grabChurns

from config import config

blp = Blueprint("historic_node", __name__, description="Historic node data API")


@blp.route('/generateReport', methods=['POST'])
def generateReport():
    """
    Generate a report for a node's performance between specified cycles
    ---
    tags:
        - Historical Node

    parameters:
      - in: body
        name: data
        required: true
        schema:
          type: object
          required:
            - start
            - end
            - node
          properties:
            start:
              type: string
            end:
              type: string
            node:
              type: string
    responses:
      200:
        description: Return historical Info on the given node.
      400:
        description: Invalid JSON data or missing required fields.
    """
    startTime = time.time()

    data = request.get_json()

    if not data:
        return jsonify({'message': 'Invalid JSON data'}), 400

    try:
        start = int(data.get('start'))
        end = int(data.get('end'))
        node = data.get('node')

        if not node or not start or not end:
            return jsonify({'message': 'Invalid JSON data or missing required fields'}), 400

        # Query for churns within the specified range
        data = (ThornodeMonitorHistoric.query
                .filter(and_(
                    ThornodeMonitorHistoric.node_address == node,
                    ThornodeMonitorHistoric.churnHeight >= start,
                    ThornodeMonitorHistoric.churnHeight <= end
                ))
                .order_by(ThornodeMonitorHistoric.churnHeight.asc())
                .all())

        if not data:
            return jsonify({'message': f'No data between churns {start}-{end}'}), 500

        # Query for global data within the specified range
        globalData = (ThornodeMonitorGlobalHistoric.query
                      .filter(and_(
                          ThornodeMonitorGlobalHistoric.churnHeight >= start,
                          ThornodeMonitorGlobalHistoric.churnHeight <= end
                      ))
                      .order_by(ThornodeMonitorGlobalHistoric.churnHeight.asc())
                      .all())

        if not globalData:
            return jsonify({'message': f'No global data between churns {start}-{end}'}), 500

        totalAward = 0
        position = 0
        maxPos = 0
        maxPosLen = 0

        for churn in data:
            totalAward += churn.current_award

            if churn.position != 0:
                maxPosLen += 1
                maxPos += churn.maxNodes
                position += churn.position

        startBlock = data[0].churnHeight
        endBlock = data[-1].churnHeight
        startBond = data[0].bond
        endBond = data[-1].bond
        bondIncrease = endBond - startBond

        if maxPosLen == 0:
            return jsonify({'message': f'No data between churns {start}-{end}'}), 500

        position = round(position / maxPosLen)
        maxPos = round(maxPos / maxPosLen)

        graphData = {
            "Xticks": [churn.churnHeight for churn in data],
            "bond": [churn.bond for churn in data],
            "rewards": [churn.current_award for churn in data],
            "position": [churn.position for churn in data],
            "maxPosition": [churn.maxNodes for churn in data]
        }

        tableData = {
            "churnHeight": [churn.churnHeight for churn in data],
            "date": [convert_date_format(global_item.date) for global_item in globalData],
            "price": [global_item.thorPrice for global_item in globalData],
            "rewards": [(churn.current_award / 100000000) for churn in data],
            "dollarValue": [(churn.current_award / 100000000) * float(global_item.thorPrice) for churn, global_item in zip(data, globalData)]
        }

        endTime = time.time()
        print(f"Execution time: {endTime - startTime}s")

        return jsonify({
            'startBlock': startBlock,
            'endBlock': endBlock,
            'startBond': startBond,
            'endBond': endBond,
            'BondIncrease': bondIncrease,
            'position': position,
            'maxPosition': maxPos,
            'totalRewards': totalAward,
            'graphData': graphData,
            'tableData': tableData
        })

    except SQLAlchemyError as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500
    except ValueError:
        return jsonify({'message': 'Invalid input types'}), 400

@blp.route('/grab-bond/<node>', methods=['GET'])
def grabBond(node=None):
    """
    Grab a node's bond over past churns
    API used to inspect the bond amount of a node over time.
    ---
    tags:
      - Historical Node
    parameters:
      - name: node
        in: path
        type: string
        required: true
        default: thor1sngd0zz6pwdx2e20sml27354vzkrwa4fnjxvnc
        description: The node to look at
    responses:
      200:
        description: The bond amount of a node over past churns
    """
    try:
        if not node:
            # Check if the node is provided in the request data
            data = request.get_json()
            if not data or 'node' not in data:
                return jsonify({'message': 'Node parameter is required'}), 400
            node = data['node']

        # Query for bond data of the specified node
        data = (ThornodeMonitorHistoric.query
                .filter(ThornodeMonitorHistoric.node_address == node)
                .order_by(ThornodeMonitorHistoric.churnHeight.asc())
                .all())

        if not data:
            return jsonify({'message': f'No bond data found for node {node}'}), 404

        interim = {churn.churnHeight: churn.bond for churn in data}

        return jsonify(interim)

    except SQLAlchemyError as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

@blp.route('/grab-slashes/<node>', methods=['GET'])
def grabSlashes(node=None):
    """
    Grab a node's slash points over past churns
    API used to inspect the bond amount of a node over time.
    ---
    tags:
      - Historical Node
    parameters:
      - name: node
        in: path
        type: string
        required: true
        default: thor1sngd0zz6pwdx2e20sml27354vzkrwa4fnjxvnc
        description: The node to look at
    responses:
      200:
        description: The slash points of a node over past churns
    """
    try:
        if not node:
            # Check if the node is provided in the request data
            data = request.get_json()
            if not data or 'node' not in data:
                return jsonify({'message': 'Node parameter is required'}), 400
            node = data['node']

        # Query for bond data of the specified node
        data = (ThornodeMonitorHistoric.query
                .filter(ThornodeMonitorHistoric.node_address == node)
                .order_by(ThornodeMonitorHistoric.churnHeight.asc())
                .all())

        if not data:
            return jsonify({'message': f'No bond data found for node {node}'}), 404

        interim = {churn.churnHeight: churn.slash_points for churn in data}

        return jsonify(interim)

    except SQLAlchemyError as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

@blp.route('/grab-rewards/<node>', methods=['GET'])
def grabSlashes(node=None):
    """
    Grab a node's rewards over past churns
    API used to inspect the bond amount of a node over time.
    ---
    tags:
      - Historical Node
    parameters:
      - name: node
        in: path
        type: string
        required: true
        default: thor1sngd0zz6pwdx2e20sml27354vzkrwa4fnjxvnc
        description: The node to look at
    responses:
      200:
        description: The reward amount of a node over past churns
    """
    try:
        if not node:
            # Check if the node is provided in the request data
            data = request.get_json()
            if not data or 'node' not in data:
                return jsonify({'message': 'Node parameter is required'}), 400
            node = data['node']

        # Query for bond data of the specified node
        data = (ThornodeMonitorHistoric.query
                .filter(ThornodeMonitorHistoric.node_address == node)
                .order_by(ThornodeMonitorHistoric.churnHeight.asc())
                .all())

        if not data:
            return jsonify({'message': f'No bond data found for node {node}'}), 404

        interim = {churn.churnHeight: churn.current_award for churn in data}

        return jsonify(interim)

    except SQLAlchemyError as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

@blp.route('/grabPosition/<node>', methods=['GET'])
def grabPositions(node=None):
    """
    Grab a node's relative performance over past churns
    API returns the position out of others based on slashes from previous churns. positions 1-max (number of nodes in churn) 1 being lowest/best.

    0 = Not active that churn
    ---
    tags:
      - Historical Node
    parameters:
        - name: node
          in: path
          type: string
          required: true
          default: thor1sngd0zz6pwdx2e20sml27354vzkrwa4fnjxvnc
          description: The node to look at
    responses:
        200:
          description: The node position compared to other active nodes over past churns
    """
    try:
        # Query for position data of the specified node
        data = (ThornodeMonitorHistoric.query
                .filter(ThornodeMonitorHistoric.node_address == node)
                .order_by(ThornodeMonitorHistoric.churnHeight.asc())
                .all())

        if not data:
            return jsonify({'message': f'No position data found for node {node}'}), 404

        interim = {
            churn.churnHeight: {
                'position': churn.position,
                'max': churn.maxNodes
            }
            for churn in data
        }

        return jsonify(interim)

    except SQLAlchemyError as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

@blp.route('/grabChurnsForNode/<node>', methods=['GET'])
def grabChurnsNode(node):
    """
    Returns a list of past churns which are indexed by the API for a given node address
    ---
    tags:
      - Historical Node
    parameters:
        - name: node
          in: path
          type: string
          required: true
          default: thor1sngd0zz6pwdx2e20sml27354vzkrwa4fnjxvnc
          description: The node to look at
    responses:
        200:
          description: List of churn heights indexes for a given node
    """
    try:
        # Query for all churns in the global historic table
        churns = (ThornodeMonitorGlobalHistoric.query
                  .with_entities(ThornodeMonitorGlobalHistoric.churnHeight, ThornodeMonitorGlobalHistoric.date)
                  .order_by(ThornodeMonitorGlobalHistoric.churnHeight.asc())
                  .all())

        # Query for churns specific to the given node
        data = (ThornodeMonitorHistoric.query
                .filter(ThornodeMonitorHistoric.node_address == node)
                .with_entities(ThornodeMonitorHistoric.churnHeight)
                .order_by(ThornodeMonitorHistoric.churnHeight.asc())
                .all())

        churn_heights_list2 = {item.churnHeight for item in data}

        filtered_list1 = [
            {
                'churnHeight': churn.churnHeight,
                'date': churn.date
            }
            for churn in churns if churn.churnHeight in churn_heights_list2
        ]

        return jsonify(filtered_list1)

    except SQLAlchemyError as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

@blp.route('/grabHistoricData/<churn>', methods=['GET'])
def grabHistoricData(churn):
    """Returns the data for all nodes on the network at the given churn height
       ---
       tags:
         - Historical
       parameters:
         - name: churn
           in: path
           type: string
           required: true
           default: 11867388
           description: The indexed churn to grab data from
       responses:
         200:
           description: List of churn heights indexed
         404:
           description: Churn height not indexed
       """
    # Query the database for entries matching the churn height
    entries = ThornodeMonitorHistoric.query.filter_by(churnHeight=churn).all()

    if not entries:
        abort(404, 'Churn height ' + str(churn) + ' not indexed')


    # Convert each entry to a dictionary using the to_dict method
    data = [entry.to_dict() for entry in entries]

    return jsonify(data)

@blp.route('/historicPerformers/<churn>', methods=['GET'])
def grabHistoricPerformers(churn):
    """Returns the data for all nodes on the network at the given churn height
           ---
           tags:
             - Historical
           parameters:
             - name: churn
               in: path
               type: string
               required: true
               default: 3
               description: The indexed churn to grab data from
           responses:
             200:
               description: List of churn heights indexed
             404:
               description: Churn height not indexed
           """

    all_churns = grabChurns().json  # Replace with your actual call
    if not isinstance(all_churns, list) or len(all_churns) == 0:
        abort(404, 'No churns data available')

    # Get the last 'churns' items
    try:
        last_churns = all_churns[-int(churn):]
    except ValueError:
        abort(400, 'Invalid churn parameter')

    outputData = {}

    for churn_data in last_churns:
        entries = ThornodeMonitorHistoric.query.filter_by(churnHeight=churn_data).all()

        if not entries:
            abort(404, f'Churn height {churn_data} not indexed')

        data = [entry.to_dict() for entry in entries]
        active_nodes = {d['node_address']: d for d in data if d['status'] == "Active"}
        outputData[churn_data] = active_nodes

    ByChurnData = {
        churn: {
            "totalBond": sum(node["bond"] for node in nodes.values()),
            "totalRewards": sum(node["current_award"] for node in nodes.values()),
            "totalSlashes": sum(node["slash_points"] for node in nodes.values()),
            "totalNodes": len(nodes),
            "Locations": list({node["location"] for node in nodes.values()}),
            "ISPs": list({node["isp"] for node in nodes.values()})
        }
        for churn, nodes in outputData.items()
    }

    perNode = {}

    for churn_nodes in outputData.values():
        for node_address, node_data in churn_nodes.items():
            if node_address not in perNode:
                perNode[node_address] = {
                    "positionRaw": node_data["position"],
                    "seenIn": 1,
                    "avg": node_data["position"]
                }
            else:
                perNode[node_address]["positionRaw"] += node_data["position"]
                perNode[node_address]["seenIn"] += 1
                perNode[node_address]["avg"] = (
                        perNode[node_address]["positionRaw"] / perNode[node_address]["seenIn"]
                )

    # Sort nodes by their average position
    sorted_nodes = sorted(perNode.items(), key=lambda x: x[1]['avg'])

    # Get the top 5 and bottom 5 node addresses
    top_five_addresses = [node[0] for node in sorted_nodes[:5]]
    bottom_five_addresses = [node[0] for node in sorted_nodes[-5:]]

    return jsonify({
        "topFive": top_five_addresses,
        "bottomFive": bottom_five_addresses
    })




