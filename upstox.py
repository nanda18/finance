import json
import requests
from datetime import datetime, timedelta
import pytz
from typing import Optional, Dict

# Use ijson for large file streaming
try:
    import ijson
except ImportError:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'ijson'])
    import ijson

NSE_JSON_PATH = 'stockanalysis/NSE.json'
UPSTOX_API_KEY = 'YOUR_UPSTOX_API_KEY'  # Replace with your Upstox API key
UPSTOX_ACCESS_TOKEN = 'YOUR_UPSTOX_ACCESS_TOKEN'  # Replace with your Upstox access token

# Hardcoded share name and datetime
TRADING_SYMBOL = 'TATAMOTORS'
# Use a past date for which historical data is available
# For minute data, history is available from Jan 2022. Max retrieval 1 month for 1-15min intervals.
TARGET_DATETIME_STR = '2024-05-14 10:00:00'  # Example: A valid past date and time
IST = pytz.timezone('Asia/Kolkata')

def get_instrument_key(trading_symbol):
    with open(NSE_JSON_PATH, 'rb') as f:
        for instrument in ijson.items(f, 'item'):
            if instrument.get('segment') == 'NSE_EQ' and instrument.get('trading_symbol') == trading_symbol:
                return instrument['instrument_key']
    return None

def fetch_historical_candle_v3(instrument_key: str, target_dt_ist: datetime) -> Optional[Dict[str, float]]:
    """
    Fetches historical candle data using Upstox Historical Candle Data V3 API.
    Tries to find the candle matching the hour and minute of target_dt_ist.
    If no exact match is found, it retrieves the nearest candle within a 1-minute gap.

    Args:
        instrument_key (str): The unique identifier for the financial instrument.
        target_dt_ist (datetime): The target datetime in IST for which to fetch the candle data.

    Returns:
        Optional[Dict[str, float]]: A dictionary containing the candle data (open, high, low, close, volume)
                                     or None if no data is found.
    """
    unit = 'minutes'  # As per your previous correction and docs
    interval_value = '1'  # For 1-minute candles
    
    # Format the date part of target_dt_ist as YYYY-MM-DD for API parameters
    date_str = target_dt_ist.strftime('%Y-%m-%d')

    # Endpoint: /historical-candle/{instrument_key}/{unit}/{interval}/{to_date}
    url = f"https://api.upstox.com/v3/historical-candle/{instrument_key}/{unit}/{interval_value}/{date_str}"
    
    headers = {
        'Accept': 'application/json',
        'Api-Version': '3.0', 
    }
    params = {
        'from_date': date_str  # Fetching for a single day
    }

    # print(f"Requesting URL: {url} with params: {params}")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f'Error fetching data from {url}: {response.status_code} {response.text}')
        return None
    
    data = response.json()
    candles = data.get('data', {}).get('candles', [])

    if not candles:
        print(f"No candles received from API for {date_str}.")
        return None

    # Target time (hour and minute) from the original target_dt_ist
    target_hour = target_dt_ist.hour
    target_minute = target_dt_ist.minute

    # Initialize variables to track the closest candle
    closest_candle = None
    closest_time_diff = float('inf')

    for candle_data in candles:
        # candle_data: [timestamp_str, open, high, low, close, volume, oi]
        try:
            candle_timestamp_str = candle_data[0]
            # Parse the timestamp string from API (which includes timezone offset)
            candle_dt = datetime.fromisoformat(candle_timestamp_str)

            # Calculate the time difference in minutes
            time_diff = abs((candle_dt - target_dt_ist).total_seconds() / 60)

            # Check for an exact match first
            if (candle_dt.hour == target_hour and candle_dt.minute == target_minute):
                return {
                    'timestamp': candle_timestamp_str,
                    'open': candle_data[1],
                    'high': candle_data[2],
                    'low': candle_data[3],
                    'close': candle_data[4],
                    'volume': candle_data[5],
                }
            # If no exact match, check if it's within 1 minute
            elif time_diff <= 1 and time_diff < closest_time_diff:
                closest_candle = {
                    'timestamp': candle_timestamp_str,
                    'open': candle_data[1],
                    'high': candle_data[2],
                    'low': candle_data[3],
                    'close': candle_data[4],
                    'volume': candle_data[5],
                }
                closest_time_diff = time_diff

        except (IndexError, ValueError) as e:
            print(f"Error parsing candle data {candle_data}: {e}")
            continue
            
    if closest_candle:
        print(f"Using closest candle data for {target_dt_ist.strftime('%H:%M')} on {date_str}.")
        return closest_candle

    print(f"No candle found for {target_dt_ist.strftime('%H:%M')} on {date_str} in the returned data.")
    return None


if __name__ == '__main__':
    instrument_key = get_instrument_key(TRADING_SYMBOL)
    print(f'Instrument key for {TRADING_SYMBOL}: {instrument_key}')

    if not instrument_key:
        print(f'Instrument key for {TRADING_SYMBOL} not found.')
    else:
        target_dt_naive = datetime.strptime(TARGET_DATETIME_STR, '%Y-%m-%d %H:%M:%S')
        target_dt_ist = IST.localize(target_dt_naive)
        
        print(f"Attempting to fetch historical data for {TRADING_SYMBOL} at {target_dt_ist.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
        
        price_data = fetch_historical_candle_v3(instrument_key, target_dt_ist)
        
        if price_data:
            print(f'Price data for {TRADING_SYMBOL} at {price_data["timestamp"]}: {price_data}')
        else:
            print(f'Could not retrieve specific price data for {TRADING_SYMBOL} at {target_dt_ist.strftime("%Y-%m-%d %H:%M IST")}.')
