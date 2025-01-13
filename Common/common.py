from datetime import datetime

def convert_date_format(input_date):
    # Convert string to datetime object
    date_object = datetime.strptime(input_date, '%d-%m-%Y')

    # Format datetime object to the desired string format
    output_date = date_object.strftime('%Y-%m-%d')

    return output_date