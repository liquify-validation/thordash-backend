from datetime import datetime, timedelta
import requests
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from API.histroic_global.models import PriceData
from DB import db

_COINGECKO_URL = 'https://api.coingecko.com/api/v3/coins/thorchain/history?date='
_MAX_RETRIES = 5


def _fetch_price_for_date(formatted_date):
    """Fetch RUNE price from CoinGecko for a given DD-MM-YYYY date string.
    Returns the USD price float, or None on failure."""
    for attempt in range(_MAX_RETRIES):
        try:
            response = requests.get(_COINGECKO_URL + formatted_date, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('market_data', {}).get('current_price', {}).get('usd')
            print(f"[price] HTTP {response.status_code} for {formatted_date} (attempt {attempt + 1})")
        except requests.RequestException as e:
            print(f"[price] Request error for {formatted_date} (attempt {attempt + 1}): {e}")
    print(f"[price] Failed to fetch {formatted_date} after {_MAX_RETRIES} attempts")
    return None


def fetch_and_store_price(app: Flask):
    """Fetches today's RUNE price and stores it in the database."""
    with app.app_context():
        date = datetime.now()
        formatted_date = date.strftime('%d-%m-%Y')

        try:
            current_price = _fetch_price_for_date(formatted_date)
            if current_price is None:
                print(f"[price] No price data found for {formatted_date}")
                return

            existing_record = PriceData.query.filter_by(date=date.date()).first()
            if existing_record:
                print(f"[price] Data for {formatted_date} already exists")
                return

            db.session.add(PriceData(date=date.date(), price=current_price))
            db.session.commit()
            print(f"[price] Inserted {formatted_date}: ${current_price}")
        except Exception as e:
            db.session.rollback()
            print(f"[price] Error for {formatted_date}: {e}")


def fetch_and_store_prices(app: Flask):
    """Fetches the past 30 days of price data and stores any missing records."""
    with app.app_context():
        today = datetime.now()

        for i in range(30):
            date = today - timedelta(days=i)
            formatted_date = date.strftime('%d-%m-%Y')

            try:
                existing_record = PriceData.query.filter_by(date=date.date()).first()
                if existing_record:
                    print(f"[price] Data for {formatted_date} already exists")
                    continue

                current_price = _fetch_price_for_date(formatted_date)
                if current_price is None:
                    print(f"[price] No price data found for {formatted_date}")
                    continue

                db.session.add(PriceData(date=date.date(), price=current_price))
                db.session.commit()
                print(f"[price] Inserted {formatted_date}: ${current_price}")
            except Exception as e:
                db.session.rollback()
                print(f"[price] Error for {formatted_date}: {e}")
