import requests
import os
from config import config
from API.nodes.models import ThornodeMonitor

def get_node_by_address(node_address):
    node = ThornodeMonitor.query.get(node_address)

    if node:
        return node.to_dict()  # Convert the node instance to a dictionary
    else:
        return None  # Return None if no record is found

def get_nodes_by_status(status):
    nodes = ThornodeMonitor.query.filter_by(status=status).all()

    # Convert the list of nodes to dictionaries
    return [node.to_dict() for node in nodes]  # Return a list of dictionaries

def get_all_nodes():
    nodes = ThornodeMonitor.query.all()

    # Convert the list of nodes to dictionaries
    return [node.to_dict() for node in nodes]  # Return a list of dictionaries