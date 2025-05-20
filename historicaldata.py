import pandas as pd
from datetime import datetime, timedelta, time
import pytz
from typing import Optional, Dict, Any
from upstox import get_instrument_key, fetch_historical_candle_v3

IST = pytz.timezone('Asia/Kolkata')

def get_price_start_time(board_time: datetime) -> datetime:
    # board_time: naive datetime in IST
    trading_start = time(9, 30)
    trading_end = time(15, 30)
    
    if board_time.time() < trading_start:
        # Before trading hours, return trading end time of the previous day
        previous_day = board_time - timedelta(days=1)
        return datetime.combine(previous_day.date(), trading_end)
    elif board_time.time() > trading_end:
        # After trading hours, return trading end time of the current day
        return datetime.combine(board_time.date(), trading_end)
    else:
        # Within trading hours, return board_time
        return board_time

def get_price_end_time(start_time: datetime) -> datetime:
    """
    Calculates the price end time based on the start time.
    The price end time is generally 40 minutes after the start time,
    but if the start time is after trading hours, it is set to the next day's trading start time.

    Args:
        start_time (datetime): The start time for the price.

    Returns:
        datetime: The calculated price end time.
    """
    trading_start = time(9, 30)  # 9:30 AM
    trading_end = time(15, 30)    # 3:30 PM

    # Calculate the initial end time (40 minutes after start time)
    initial_end_time = start_time + timedelta(minutes=40)

    # Check if the start time is after trading hours
    if start_time.time() > trading_end:
        # Set to the next day's trading start time
        next_day = start_time + timedelta(days=1)
        return datetime.combine(next_day.date(), trading_start)

    # Check if the initial end time is within trading hours
    if initial_end_time.time() > trading_end:
        # If it exceeds trading hours, set it to the end of trading hours
        return datetime.combine(initial_end_time.date(), trading_end)
    
    return initial_end_time

def fetch_candle_details(nse_id: str, dt: datetime) -> Optional[Dict[str, Any]]:
    instrument_key = get_instrument_key(nse_id)
    if not instrument_key:
        print(f"Instrument key not found for {nse_id}")
        return None
    dt_ist = IST.localize(dt)
    candle = fetch_historical_candle_v3(instrument_key, dt_ist)
    if candle:
        return {
            'timestamp': candle['timestamp'],
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close'],
            'volume': candle['volume']
        }
    return None

def fetch_price_details_for_row(row: pd.Series) -> pd.Series:
    nse_id = row['nse_id']
    board_time = row['board_announcement_time']
    if pd.isnull(board_time):
        print(f"Skipping {nse_id} due to invalid board_announcement_time")
        return pd.Series([None] * 12, index=[
            'start_timestamp', 'start_open', 'start_high', 'start_low', 'start_close', 'start_volume',
            'end_timestamp', 'end_open', 'end_high', 'end_low', 'end_close', 'end_volume'
        ])
    price_start_time = get_price_start_time(board_time)
    price_end_time = get_price_end_time(board_time)
    start_candle = fetch_candle_details(nse_id, price_start_time)
    end_candle = fetch_candle_details(nse_id, price_end_time)
    return pd.Series([
        start_candle['timestamp'] if start_candle else None,
        start_candle['open'] if start_candle else None,
        start_candle['high'] if start_candle else None,
        start_candle['low'] if start_candle else None,
        start_candle['close'] if start_candle else None,
        start_candle['volume'] if start_candle else None,
        end_candle['timestamp'] if end_candle else None,
        end_candle['open'] if end_candle else None,
        end_candle['high'] if end_candle else None,
        end_candle['low'] if end_candle else None,
        end_candle['close'] if end_candle else None,
        end_candle['volume'] if end_candle else None,
    ], index=[
        'start_timestamp', 'start_open', 'start_high', 'start_low', 'start_close', 'start_volume',
        'end_timestamp', 'end_open', 'end_high', 'end_low', 'end_close', 'end_volume'
    ])

if __name__ == "__main__":
    # Load the Excel file
    df = pd.read_excel('./stockanalysis/stock_analysis_results.xlsx')
    # df = df[:10]
    # Ensure 'nse_id' and 'board_announcement_time' columns exist and are datetime
    df['board_announcement_time'] = pd.to_datetime(df['exchdisstime'], errors='coerce')  # Convert to datetime, coerce errors to NaT
    
    # Check for NaT values and handle them
    if df['board_announcement_time'].isnull().any():
        print("Warning: Some board announcement times could not be converted to datetime.")
        print(df[df['board_announcement_time'].isnull()])  # Print rows with NaT values

    # Apply the function and expand the results into separate columns
    df[
        [
            'start_timestamp', 'start_open', 'start_high', 'start_low', 'start_close', 'start_volume',
            'end_timestamp', 'end_open', 'end_high', 'end_low', 'end_close', 'end_volume'
        ]
    ] = df.apply(fetch_price_details_for_row, axis=1)
    
    # Print the relevant columns
    print(df[
        [
            'nse_id', 'board_announcement_time',
            'start_timestamp', 'start_open', 'start_high', 'start_low', 'start_close', 'start_volume',
            'end_timestamp', 'end_open', 'end_high', 'end_low', 'end_close', 'end_volume'
        ]
    ])
    df.to_csv('stock_analysis_dummy.csv', index=False)