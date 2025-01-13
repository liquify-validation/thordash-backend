import requests
import os
from config import config
from API.network.models import ThornodeMonitorGlobal

def get_feild(field_name):
    # Fetch the first (and only) record
    record = ThornodeMonitorGlobal.query.first()

    if record:
        # Check if the requested field exists on the record
        if hasattr(record, field_name):
            # Return the requested field value
            return getattr(record, field_name)
        else:
            return None
    else:
        return None

def get_network_info():
    # Fetch the first (and only) record
    record = ThornodeMonitorGlobal.query.first()

    if record:
        return record.to_json()
    else:
        return None