from datetime import datetime

def convert_date_format(input_date):
    """Convert a date string from DD-MM-YYYY to YYYY-MM-DD format.
    Returns the original string unchanged if it cannot be parsed."""
    try:
        date_object = datetime.strptime(input_date, '%d-%m-%Y')
        return date_object.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return input_date