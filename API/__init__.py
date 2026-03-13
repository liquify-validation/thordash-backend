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
from API.vaults import VaultBlueprint
from API.mimir import MimirBlueprint
from API.pools import PoolBlueprint
from API.queue import QueueBlueprint
from API.nodes.task import run_every_minuite
from API.histroic_global.task import fetch_and_store_prices, fetch_and_store_price
from API.vaults.task import sync_vaults_scheduled
from API.mimir.task import sync_mimir_scheduled, sync_mimir_votes_scheduled
from API.pools.task import sync_pools_scheduled
from API.queue.task import sync_queue_scheduled
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
        db.create_all()

        scheduler = BackgroundScheduler()
        scheduler.start()
        # scheduler.add_job(func=run_every_minuite, trigger=IntervalTrigger(minutes=1), args=[app])
        scheduler.add_job(func=fetch_and_store_price,  trigger="cron", hour=23, minute=59, args=[app])
        scheduler.add_job(func=sync_vaults_scheduled,  trigger=IntervalTrigger(minutes=5),  args=[app])
        scheduler.add_job(func=sync_mimir_scheduled,   trigger=IntervalTrigger(minutes=10), args=[app])
        scheduler.add_job(func=sync_mimir_votes_scheduled, trigger=IntervalTrigger(minutes=10), args=[app])
        scheduler.add_job(func=sync_pools_scheduled,   trigger=IntervalTrigger(minutes=2),  args=[app])
        scheduler.add_job(func=sync_queue_scheduled,   trigger=IntervalTrigger(minutes=1),  args=[app])

    app.register_blueprint(NetworkBlueprint, url_prefix='/network')
    app.register_blueprint(NodeBlueprint, url_prefix='/nodes')
    app.register_blueprint(HistoricNodeBlueprint, url_prefix='/historic/node')
    app.register_blueprint(HistoricNetworkBlueprint, url_prefix='/historic/network')
    app.register_blueprint(VaultBlueprint, url_prefix='/vaults')
    app.register_blueprint(MimirBlueprint, url_prefix='/mimir')
    app.register_blueprint(PoolBlueprint, url_prefix='/pools')
    app.register_blueprint(QueueBlueprint, url_prefix='/queue')


    return app