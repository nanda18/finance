import json
import pandas as pd

def load_nse_symbols(nse_file_path):
    with open(nse_file_path, 'r') as file:
        nse_data = json.load(file)
        return {entry.get('trading_symbol') for entry in nse_data}  # Create a set of trading symbols

def load_nse_ids_from_excel(excel_file_path):
    df = pd.read_excel(excel_file_path)
    return df['nse_id'].tolist()  # Adjust the column name as necessary

def check_symbols_exist(nse_ids, nse_symbols):
    print("num nse trading sumbols", len(nse_symbols))
    print("num nse ids", len(nse_ids))
    return all(nse_id in nse_symbols for nse_id in nse_ids)

if __name__ == "__main__":
    nse_file_path = './stockanalysis/NSE.json'  # Path to NSE.json
    excel_file_path = './stock_analysis_results.xlsx'  # Path to the Excel file

    nse_symbols = load_nse_symbols(nse_file_path)
    nse_ids = load_nse_ids_from_excel(excel_file_path)

    if check_symbols_exist(nse_ids, nse_symbols):
        print("All NSE IDs exist in NSE.json.")
    else:
        print("Some NSE IDs do not exist in NSE.json.")
