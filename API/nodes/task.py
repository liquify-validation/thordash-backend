import os
from config import config
from API.nodes.models import ThornodeMonitor
import json
import requests
import time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from DB import db
from flask import current_app, Flask
from sqlalchemy.exc import IntegrityError
import random

def updateIPs():
    currentDBData = ThornodeMonitor.query.all()

    # Build the old IP table from the database
    ipTableOld = {node.node_address: node.ip_address for node in currentDBData}

    # Fetch the new node data from the API
    response_API = requests.get('https://thornode.ninerealms.com/thorchain/nodes')
    newData = json.loads(response_API.text)
    ipTableNew = {node['node_address']: node['ip_address'] for node in newData}

    # Check for mismatches between old and new IPs
    mismatch = {key: ipTableNew[key] for key in ipTableNew if key in ipTableOld and ipTableNew[key] != ipTableOld[key]}

    for node_address, new_ip in mismatch.items():
        if new_ip:
            response_code = 0
            ip_data = {}

            while response_code != 200:
                response = requests.get(f"http://ip-api.com/json/{new_ip}")
                response_code = response.status_code

                if response_code == 429:
                    print("Rate limited, wait 60 seconds")
                    time.sleep(60)
                elif response_code == 200:
                    ip_data = json.loads(response.text)

            # Update only if the API response status is not "fail"
            if ip_data.get('status') != "fail":
                location = ip_data.get('city', "")
                isp = ip_data.get('isp', "")
            else:
                location = ""
                isp = ""

            try:
                # Fetch the record from the database to update
                node = ThornodeMonitor.query.filter_by(node_address=node_address).first()

                if node:
                    node.ip_address = new_ip
                    node.location = location
                    node.isp = isp

                    db.session.commit()  # Commit the changes to the database
                    print(f"Updated node {node_address}: IP {new_ip}, Location {location}, ISP {isp}")

            except SQLAlchemyError as e:
                db.session.rollback()  # Rollback in case of an error
                print(f"Database error: {e}")

def grabLatestBlockHeight(nodes, max_retries=10):
    """
    grabLatestBlockHeight looks at up to 3 random nodes in the active pool and returns the max height.

    :param nodes: all thor nodes currently on the network pulled from ninerelms api
    :param max_retries: maximum number of attempts before giving up
    :return: the latest block height, or 0 if all attempts fail
    """
    activeNodes = [x for x in nodes if x['status'] == "Active"]
    if not activeNodes:
        print("[nodes] No active nodes available to query block height")
        return 0

    sample_size = min(3, len(activeNodes))

    for attempt in range(max_retries):
        randomOffsets = random.sample(range(len(activeNodes)), sample_size)
        status = []
        for offset in randomOffsets:
            try:
                response = requests.get(f'http://{activeNodes[offset]["ip_address"]}:27147/status?', timeout=5)
                if response.status_code == 200:
                    status.append(response.json())
            except requests.exceptions.RequestException:
                print(f"[nodes] Request timed out for node (attempt {attempt + 1})")

        if status:
            blocks = [x['result']['sync_info']['latest_block_height'] for x in status]
            return max(blocks)

    print(f"[nodes] Failed to get block height after {max_retries} attempts")
    return 0


def splitNodes(nodes):
    """
    splitNodes compares the list of nodes currently in the DB and what is returned by the ninerelms API

    :param nodes: all thor nodes currently on the network pulled from the ninerelms API
    :return dataForExistingNodes: list of nodes already in our DB
    :return dataForNewNodes: list of nodes not already in our DB
    """
    # Query current DB data for all node addresses
    currentDBData = ThornodeMonitor.query.with_entities(ThornodeMonitor.node_address).all()

    # Flatten the result into a list of node addresses
    currentAddrList = [address[0] for address in currentDBData]

    # Full list of node addresses from the API
    fullAddrList = [x['node_address'] for x in nodes]

    # Identify new nodes by comparing the lists
    newList = set(fullAddrList).difference(set(currentAddrList))

    # Separate the nodes into existing and new ones
    dataForExistingNodes = [x for x in nodes if x['node_address'] in currentAddrList]
    dataForNewNodes = [x for x in nodes if x['node_address'] in newList]

    return dataForExistingNodes, dataForNewNodes

def gradDataAndSaveToDB():
    """
    gradDataAndSaveToDB used to update thornode_monitor_global and thornode_monitor databases
    """
    # Grab nodes from the API
    response_API = requests.get('https://thornode.ninerealms.com/thorchain/nodes')
    data = response_API.json()  # Convert response to JSON

    # Sanitize data, remove any empty elements
    nodes = [x for x in data if x['node_address'] != '']

    # Grab the latest block height
    maxHeight = grabLatestBlockHeight(nodes)

    # Update thornode_monitor_global with maxHeight
    # global_record = ThornodeMonitorGlobal.query.get(1)  # Assuming there is only one record with primary_key = 1
    # if global_record:
    #     global_record.maxHeight = maxHeight
    #     db.session.commit()

    # Split nodes into existing and new ones
    dataForExistingNodes, dataForNewNodes = splitNodes(nodes)

    # Prepare lists for bulk update/insert
    update_mappings = []
    insert_mappings = []

    # Handle existing nodes
    for node in dataForExistingNodes:
        try:
            bond_providersString = ",".join([provider["bond_address"] for provider in node['bond_providers']['providers']])
        except TypeError:
            bond_providersString = ""

        is_jailed = 0
        try:
            if len(node['jail']) > 0 and 'release_height' in node['jail']:
                if node['jail']['release_height'] > int(maxHeight):
                    is_jailed = 1
        except TypeError:
            pass

        # Add to update mappings
        update_mappings.append({
            'node_address': node['node_address'],
            'active_block_height': node['active_block_height'],
            'bond_providers': json.dumps(node['bond_providers']),
            'bond': int(node['total_bond']),
            'current_award': int(node['current_award']),
            'slash_points': node['slash_points'],
            'forced_to_leave': int(node['forced_to_leave']),
            'requested_to_leave': int(node['requested_to_leave']),
            'jail': json.dumps(node['jail']),
            'observe_chains': json.dumps(node['observe_chains']),
            'preflight_status': json.dumps(node['preflight_status']),
            'status': node['status'],
            'status_since': node['status_since'],
            'bondProvidersString': bond_providersString,
            'version': node['version'],
            'is_jailed': is_jailed
        })

    # Perform bulk update
    db.session.bulk_update_mappings(ThornodeMonitor, update_mappings)

    # Handle new nodes (IP-related tasks)
    ip_api_url = "http://ip-api.com/json/"
    for node in dataForNewNodes:
        if node['ip_address'] != "":
            try:
                # Fetch IP data with limited retries
                response = requests.get(ip_api_url + node['ip_address'])
                if response.status_code == 200:
                    ip_data = response.json()
                    node['ip_data'] = ip_data
                else:
                    # Fallback to empty IP data if no successful response
                    node['ip_data'] = {'city': "", 'isp': "", 'country': "", 'countryCode': ""}
            except requests.RequestException:
                node['ip_data'] = {'city': "", 'isp': "", 'country': "", 'countryCode': ""}
        else:
            node['ip_data'] = {'city': "", 'isp': "", 'country': "", 'countryCode': ""}

        # Add to insert mappings
        insert_mappings.append({
            'node_address': node['node_address'],
            'ip_address': node['ip_address'],
            'location': node['ip_data']['city'],
            'isp': node['ip_data']['isp'],
            'active_block_height': node['active_block_height'],
            'bond_providers': json.dumps(node['bond_providers']),
            'bond': int(node['total_bond']),
            'current_award': int(node['current_award']),
            'slash_points': node['slash_points'],
            'forced_to_leave': int(node['forced_to_leave']),
            'requested_to_leave': int(node['requested_to_leave']),
            'jail': json.dumps(node['jail']),
            'observe_chains': json.dumps(node['observe_chains']),
            'preflight_status': json.dumps(node['preflight_status']),
            'status': node['status'],
            'status_since': node['status_since'],
            'version': node['version'],
            'country': node['ip_data']['country'],
            'country_code': node['ip_data']['countryCode']
        })

    # Perform bulk insert
    db.session.bulk_insert_mappings(ThornodeMonitor, insert_mappings)

    # Commit all changes in one transaction
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise


def run_every_minuite(app: Flask):
    with app.app_context():
        start = time.time()
        gradDataAndSaveToDB()
        end = time.time()
        print(end - start)
        updateIPs()
