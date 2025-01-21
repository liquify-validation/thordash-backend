from datetime import datetime, timedelta
import requests
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from API.histroic_global.models import PriceData
from DB import db

def fetch_and_store_price(app: Flask):
    with app.app_context():
        """Fetches the past 30 days of price data and stores it in the database."""
        base_url = 'https://api.coingecko.com/api/v3/coins/thorchain/history?date='
        date = datetime.now()

        formatted_date = date.strftime('%d-%m-%Y')

        try:
            status = 0
            while status != 200:
                response = requests.get(base_url + formatted_date)
                status = response.status_code
            if response.status_code == 200:
                data = response.json()
                market_data = data.get('market_data', {})
                current_price = market_data.get('current_price', {}).get('usd', None)

                if current_price is not None:
                    # Check if the record for this date already exists
                    existing_record = PriceData.query.filter_by(date=date.date()).first()
                    if not existing_record:
                        # Insert the data into the database
                        new_entry = PriceData(date=date.date(), price=current_price)
                        db.session.add(new_entry)
                        db.session.commit()
                        print(f"Inserted data for {formatted_date}: ${current_price}")
                    else:
                        print(f"Data for {formatted_date} already exists in the database.")
                else:
                    print(f"No price data found for {formatted_date}.")
            else:
                print(f"Failed to fetch data for {formatted_date}, status code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching data for {formatted_date}: {str(e)}")


def fetch_and_store_prices(app: Flask):
    with app.app_context():
        """Fetches the past 30 days of price data and stores it in the database."""
        base_url = 'https://api.coingecko.com/api/v3/coins/thorchain/history?date='
        today = datetime.now()

        for i in range(30):
            date = today - timedelta(days=i)
            formatted_date = date.strftime('%d-%m-%Y')
            try:
                status = 0
                while status != 200:
                    response = requests.get(base_url + formatted_date)
                    status = response.status_code
                if response.status_code == 200:
                    data = response.json()
                    market_data = data.get('market_data', {})
                    current_price = market_data.get('current_price', {}).get('usd', None)

                    if current_price is not None:
                        # Check if the record for this date already exists
                        existing_record = PriceData.query.filter_by(date=date.date()).first()
                        if not existing_record:
                            # Insert the data into the database
                            new_entry = PriceData(date=date.date(), price=current_price)
                            db.session.add(new_entry)
                            db.session.commit()
                            print(f"Inserted data for {formatted_date}: ${current_price}")
                        else:
                            print(f"Data for {formatted_date} already exists in the database.")
                    else:
                        print(f"No price data found for {formatted_date}.")
                else:
                    print(f"Failed to fetch data for {formatted_date}, status code: {response.status_code}")
            except Exception as e:
                print(f"Error fetching data for {formatted_date}: {str(e)}")