import csv
from datetime import datetime, time as dtime
import pytz

INPUT_CSV = 'stockanalysis/annnouncements-nse_with_price_diff.csv'
OUTPUT_CSV = 'stockanalysis/filtered_announcements.csv'
TRADING_START = dtime(9, 30)
TRADING_END = dtime(15, 30)
IST = pytz.timezone('Asia/Kolkata')

def is_within_trading_hours(dt):
    """Check if the given datetime is within trading hours."""
    return TRADING_START <= dt.time() <= TRADING_END

def parse_datetime(dt_str):
    """Parse datetime string with multiple formats."""
    for fmt in ('%Y-%m-%d %H:%M:%S', '%d-%b-%Y %H:%M:%S'):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Date '{dt_str}' is not in a recognized format")

def main():
    with open(INPUT_CSV, newline='', encoding='utf-8-sig') as infile, \
         open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames  # Keep the same headers
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            # Parse the dissemination time
            diss_str = row['DISSEMINATION'].strip()
            try:
                diss_dt_naive = parse_datetime(diss_str)
                diss_dt = IST.localize(diss_dt_naive)
            except Exception as e:
                print(f"Skipping row due to date parse error: {e}")
                continue
            
            # Check if the dissemination time is within trading hours
            if is_within_trading_hours(diss_dt):
                writer.writerow(row)

if __name__ == '__main__':
    main()