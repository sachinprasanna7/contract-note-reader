# modules/angelone.py
import pdfplumber
from utils import download_attachments, get_broker_password
import os
from datetime import datetime

ANGELONE_SEARCH_QUERY = 'from:ks.etrade@angelone.com subject:"Contract Note" has:attachment newer_than:2d'

def extract_data_from_pdf(filepath):
    password = get_broker_password("angelone")
    if not password:
        return

    print(f"\n--- Processing: {filepath} ---")
    
    # Extract date from filename
    filename = os.path.basename(filepath)
    contract_note_type = "Commodity" if "Comm" in filename else "F&O"
    raw_date = filename.split('_')[2].replace('.pdf', '')
    trade_date = datetime.strptime(raw_date, '%d%m%Y').strftime('%Y-%m-%d')

    net_obligation = None
    pay_in_pay_out = None
    final_amount = None
    brokerage = 0.0
    taxes_and_charges = 0.0

    try:
        with pdfplumber.open(filepath, password=password) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()

                for table in tables:
                    for row in table:
                        clean_row = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                        
                        if not clean_row:
                            continue

                        # --- 1. Extract Net Obligation Before Levies ---
                        # In Commodity it's '(NET TOTAL)', in Equity it's 'Total'. 
                        # We check clean_row[1] == '' to avoid grabbing sub-totals later in the document.
                        if clean_row[0] in ['(NET TOTAL)', 'Total'] and clean_row[1] == '':
                            if net_obligation is None: # Only grab the first instance
                                val = clean_row[7].replace(',', '')
                                if val:
                                    net_obligation = float(val)

                        # --- 2. Extract Pay In/Out & Final Billed Amount ---
                        if clean_row[0] == 'TOTAL(NET)':
                            pay_in_val = clean_row[1].replace(',', '')
                            final_val = clean_row[-1].replace(',', '')
                            
                            if pay_in_val and final_val:
                                pay_in_pay_out = float(pay_in_val)
                                final_amount = float(final_val)

        # --- Calculate and Print ---
        if None not in (net_obligation, pay_in_pay_out, final_amount):
            # Using abs() ensures positive expense values for both profit and loss days
            brokerage = round(abs(pay_in_pay_out - net_obligation), 2)
            taxes_and_charges = round(abs(final_amount - pay_in_pay_out), 2)

            print(f"Contract Note Type: {contract_note_type}")
            print(f"Trade Date: {trade_date}")
            print(f"Net Obligation: {net_obligation}")
            print(f"Brokerage: {brokerage}")
            print(f"Taxes and Charges: {taxes_and_charges}")
        else:
            print("Error: Could not locate all required fields for calculation.")

    except Exception as e:
        print(f"Failed to open or process {filepath}. Error: {e}")

def process_angelone(gmail_service):
    """Main workflow for Angel One"""
    #files = fetch_daily_contract_note(gmail_service)

    main_folder = 'downloads/angelone'
    if not os.path.exists(main_folder):
        os.makedirs(main_folder)
    
    # loop through all files in the folder
    files = []
    for filename in os.listdir(main_folder):
        if filename.endswith('.pdf'):
            files.append(os.path.join(main_folder, filename))

    for file in files:
        extract_data_from_pdf(file)