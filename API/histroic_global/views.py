from flask_smorest import Blueprint, abort
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from API.histroic_global.models import ThornodeMonitorGlobalHistoric, PriceData
from datetime import datetime, timedelta


blp = Blueprint("historic_global", __name__, description="Historic network data API")

@blp.route('/totalBond', methods=['GET'])
def grabtotalBond():
    """
    Returns the Total Bonded rune over past churns
    ---
    tags:
      - Historical Network
    responses:
        200:
          description: the total bonded rune over past churns
    """
    try:
        # Query to fetch total bonded rune data from the global historic table
        globalData = (ThornodeMonitorGlobalHistoric.query
                      .order_by(ThornodeMonitorGlobalHistoric.churnHeight.asc())
                      .all())

        stakeData = {
            item.churnHeight: item.totalBondedRune for item in globalData
        }

        return jsonify(stakeData)

    except SQLAlchemyError as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

@blp.route('/maxEffectiveStake', methods=['GET'])
def maxEffectiveStake():
    """
    Returns the max effective stake over past churns
    ---
    tags:
      - Historical Network
    responses:
        200:
          description: max effective stake over past churns
    """
    try:
        # Query to fetch max effective stake data from the global historic table
        globalData = (ThornodeMonitorGlobalHistoric.query
                      .order_by(ThornodeMonitorGlobalHistoric.churnHeight.asc())
                      .all())

        stakeData = {
            item.churnHeight: item.maxEffectiveStake for item in globalData
        }

        return jsonify(stakeData)

    except SQLAlchemyError as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

@blp.route('/v2/grabChurns', methods=['GET'])
def grabChurnsV2():
    """
    Returns a list of past churns which are indexed by the API
    ---
    tags:
      - Historical Network
    responses:
        200:
          description: List of churn heights indexed
    """
    try:
        # Query for all churns in the global historic table
        churns = (ThornodeMonitorGlobalHistoric.query
                  .with_entities(ThornodeMonitorGlobalHistoric.churnHeight, ThornodeMonitorGlobalHistoric.date)
                  .order_by(ThornodeMonitorGlobalHistoric.churnHeight.asc())
                  .all())

        result = [
            {
                'churnHeight': churn.churnHeight,
                'date': churn.date
            }
            for churn in churns
        ]

        return jsonify(result)

    except SQLAlchemyError as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

@blp.route('/grabChurns', methods=['GET'])
def grabChurns():
    """
    Returns a list of past churns which are indexed by the API
    ---
    tags:
      - Historical Network
    responses:
        200:
          description: List of churn heights indexed
    """
    try:
        # Query for distinct churn heights in the historic table
        churns = (ThornodeMonitorGlobalHistoric.query
                  .with_entities(ThornodeMonitorGlobalHistoric.churnHeight)
                  .distinct()
                  .order_by(ThornodeMonitorGlobalHistoric.churnHeight.asc())
                  .all())

        churnData = [item.churnHeight for item in churns]

        return jsonify(churnData)

    except SQLAlchemyError as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500

@blp.route('/grabPrice', methods=['GET'])
def grabPrice():
    """
    Returns a list of price data which are indexed by the API
    ---
    tags:
      - Historical Network
    responses:
        200:
          description: List of churn heights indexed
    """
    """Fetches price data from the last 14 days from the database."""
    try:
        # Calculate the date 14 days ago
        today = datetime.now().date()
        start_date = today - timedelta(days=28)

        # Query the database for records within the last 14 days
        prices = PriceData.query.filter(PriceData.date >= start_date).order_by(PriceData.date).all()

        # Convert the results to a list of dictionaries
        price_list = [price.to_dict() for price in prices]

        # Return the data as a JSON response
        return jsonify({
            "status": "success",
            "data": price_list
        }), 200
    except Exception as e:
        # Handle errors and return a 500 response
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500