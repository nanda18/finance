import sys
from datetime import datetime
import pytz
from typing import List, Dict, Optional
from upstox import get_instrument_key, fetch_historical_candle_v3, IST


def get_prices_for_times(trading_symbol: str, datetime_strs: List[str]) -> List[Optional[Dict]]:
    """
    Given a trading symbol and a list of datetime strings (in 'YYYY-MM-DD HH:MM:SS' IST),
    return a list of price data dicts (or None if not found) for each time.
    """
    instrument_key = get_instrument_key(trading_symbol)
    if not instrument_key:
        print(f"Instrument key for {trading_symbol} not found.")
        return [None] * len(datetime_strs)

    results = []
    for dt_str in datetime_strs:
        try:
            dt_naive = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            dt_ist = IST.localize(dt_naive)
            price_data = fetch_historical_candle_v3(instrument_key, dt_ist)
            results.append(price_data)
        except Exception as e:
            print(f"Error processing {dt_str}: {e}")
            results.append(None)
    return results


def main():
    if len(sys.argv) < 3:
        print("Usage: python get_prices_for_times.py <TRADING_SYMBOL> <YYYY-MM-DD HH:MM:SS> [<YYYY-MM-DD HH:MM:SS> ...]")
        sys.exit(1)
    trading_symbol = sys.argv[1]
    datetime_strs = sys.argv[2:]
    prices = get_prices_for_times(trading_symbol, datetime_strs)
    for dt_str, price in zip(datetime_strs, prices):
        print(f"{dt_str}: {price}")

if __name__ == '__main__':
    main() 