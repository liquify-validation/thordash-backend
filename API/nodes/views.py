import traceback
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token
from sqlalchemy.exc import SQLAlchemyError
from flask import request, jsonify
import json
from flask_smorest import Blueprint, abort
import requests
import string
import bcrypt
import random
import time
import uuid
import secrets
from config.config import Config
from datetime import datetime, timezone
from DB import db
from API.nodes.service import *

from config import config

blp = Blueprint("nodes", __name__, description="Node API")

@blp.route('/node=<node>', methods=['GET'])
def grab_node(node):
    """Grab a nodes current data
           API used to inspect a nodes current state
           ---
           tags:
             - nodes
           parameters:
             - name: node
               in: path
               type: string
               required: true
               default: thor1sngd0zz6pwdx2e20sml27354vzkrwa4fnjxvnc
               description: The node to look at
           responses:
             200:
               description: nodes current state
           """
    data = get_node_by_address(node)

    if data:
        return data
    else:
        return jsonify({"error": "No record found"}), 404

@blp.route('/getActive', methods=['GET'])
def grab_node():
    """Grab a nodes current data
           API used to inspect a nodes current state
           ---
           tags:
             - nodes
           responses:
             200:
               description: nodes current state
           """
    data = get_nodes_by_status("Active")

    if data:
        return data
    else:
        return jsonify({"error": "No record found"}), 404

@blp.route('/getStandby', methods=['GET'])
def grab_standby():
    """Grab a nodes current data
           API used to inspect a nodes current state
           ---
           tags:
             - nodes
           responses:
             200:
               description: nodes current state
           """
    data = get_nodes_by_status("Standby")

    if data:
        return data
    else:
        return jsonify({"error": "No record found"}), 404

@blp.route('/getDisabled', methods=['GET'])
def grab_disabled():
    """Grab a nodes current data
           API used to inspect a nodes current state
           ---
           tags:
             - nodes
           responses:
             200:
               description: nodes current state
           """
    data = get_nodes_by_status("Disabled")

    if data:
        return data
    else:
        return jsonify({"error": "No record found"}), 404

@blp.route('/getWhitelisted', methods=['GET'])
def grab_whitelisted():
    """Grab a nodes current data
           API used to inspect a nodes current state
           ---
           tags:
             - nodes
           responses:
             200:
               description: nodes current state
           """
    data = get_nodes_by_status("Whitelisted")

    if data:
        return data
    else:
        return jsonify({"error": "No record found"}), 404

@blp.route('/getAllNodes', methods=['GET'])
def grab_nodes():
    """Grab a nodes current data
           API used to inspect a nodes current state
           ---
           tags:
             - nodes
           responses:
             200:
               description: nodes current state
           """
    data = get_all_nodes()

    if data:
        return data
    else:
        return jsonify({"error": "No record found"}), 404