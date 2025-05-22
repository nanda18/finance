import csv
from datetime import datetime, timedelta, time as dtime
import pytz
from get_prices_for_times import get_prices_for_times
from upstox import IST

ANNOUNCEMENTS_CSV = 'stockanalysis/annnouncements-nse.csv'
OUTPUT_CSV = 'stockanalysis/annnouncements-nse_with_price_diff.csv'
TRADING_START = dtime(9, 30)
TRADING_END = dtime(15, 30)
WEEKDAYS = set(range(0, 5))  # Monday=0, ..., Friday=4


def is_trading_day(dt):
    return dt.weekday() in WEEKDAYS

def get_trading_start(dt):
    return dt.replace(hour=9, minute=30, second=0, microsecond=0)

def get_trading_end(dt):
    return dt.replace(hour=15, minute=30, second=0, microsecond=0)

def adjust_to_trading_time(dt, after=True):
    # If after=True, move to next trading start if outside hours; else move to last trading time
    if not is_trading_day(dt):
        current_dt = dt
        if after:
            # Move forward to the next weekday
            while not is_trading_day(current_dt):
                current_dt += timedelta(days=1)
            return get_trading_start(current_dt)
        else:
            # Move backward to the previous weekday
            while not is_trading_day(current_dt):
                current_dt -= timedelta(days=1)
            return get_trading_end(current_dt)

    if dt.time() < TRADING_START:
        # Before trading hours on a trading day
        if after:
            # For 'after', adjust to the start of the same trading day
            return get_trading_start(dt)
        else:
            # For 'before', fallback to previous trading day's end
            current_dt = dt - timedelta(days=1)
            while not is_trading_day(current_dt):
                current_dt -= timedelta(days=1)
            return get_trading_end(current_dt)

    if dt.time() > TRADING_END:
        # After trading hours on a trading day
        if after:
            # For 'after', move to the next trading day's start
            current_dt = dt + timedelta(days=1)
            while not is_trading_day(current_dt):
                current_dt += timedelta(days=1)
            return get_trading_start(current_dt)
        else:
            # For 'before', adjust to the end of the same trading day
            return get_trading_end(dt)

    # Within trading hours
    return dt

def parse_datetime(dt_str):
    for fmt in ('%Y-%m-%d %H:%M:%S', '%d-%b-%Y %H:%M:%S'):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date '{dt_str}' is not in a recognized format")

def main():
    with open(ANNOUNCEMENTS_CSV, newline='', encoding='utf-8-sig') as infile, \
         open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['start_time', 'end_time', 'start_close', 'end_close', 'pct_diff']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            if row['SUBJECT'].strip() != 'Bagging/Receiving of orders/contracts':
                continue
            symbol = row['SYMBOL'].strip()
            diss_str = row['DISSEMINATION'].strip()
            try:
                diss_dt_naive = parse_datetime(diss_str)
                diss_dt = IST.localize(diss_dt_naive)
            except Exception as e:
                print(f"Skipping row due to date parse error: {e}")
                continue
            # Start time: 1 min after dissemination, adjusted if needed
            start_dt = diss_dt + timedelta(minutes=1)
            start_dt = adjust_to_trading_time(start_dt, after=False)
            # End time: 1 hr after dissemination, adjusted if needed
            end_dt = diss_dt + timedelta(hours=1)
            end_dt = adjust_to_trading_time(end_dt, after=True)
            # Get close prices
            start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
            end_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')
            prices = get_prices_for_times(symbol, [start_str, end_str])
            start_close = prices[0]['close'] if prices[0] else None
            end_close = prices[1]['close'] if prices[1] else None
            pct_diff = None
            if start_close and end_close:
                try:
                    pct_diff = ((end_close - start_close) / start_close) * 100
                except Exception:
                    pct_diff = None
            row.update({
                'start_time': start_str,
                'end_time': end_str,
                'start_close': start_close,
                'end_close': end_close,
                'pct_diff': pct_diff
            })
            writer.writerow(row)

if __name__ == '__main__':
    main() 