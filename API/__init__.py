import logging
import os
from flask import Flask, jsonify, redirect
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from passlib.hash import pbkdf2_sha256
from flaskTemplate import template as flaskTemplate
from flaskTemplate import swagger_config as swaggerConfig
from flask_cors import CORS, cross_origin
from flasgger import Swagger
from flask_migrate import Migrate
from API.network import NetworkBlueprint
from API.nodes import NodeBlueprint
from API.historic_nodes import HistoricNodeBlueprint
from API.histroic_global import HistoricNetworkBlueprint
from API.nodes.task import run_every_minuite
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from dotenv import load_dotenv

load_dotenv()


from config import config


def create_flask_app(db, db_url=None):
    app = Flask(__name__)
    # setup_oauth(app)
    swagger = Swagger(app, template=flaskTemplate, config=swaggerConfig)
    CORS(app)

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    logger.info('Flask app starting...')

    app.config.from_object(config.Config)
    db.init_app(app)
    migrate = Migrate(app, db)

    api = Api(app)

    with app.app_context():
        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.add_job(func=run_every_minuite, trigger=IntervalTrigger(minutes=1), args=[app])

    app.register_blueprint(NetworkBlueprint, url_prefix='/network')
    app.register_blueprint(NodeBlueprint, url_prefix='/nodes')
    app.register_blueprint(HistoricNodeBlueprint, url_prefix='/historic/node')
    app.register_blueprint(HistoricNetworkBlueprint, url_prefix='/historic/network')

    return app