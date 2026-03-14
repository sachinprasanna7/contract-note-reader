# modules/kotak.py
import pdfplumber
from utils import download_attachments, get_broker_password
import os
from datetime import datetime

KOTAK_SEARCH_QUERY = 'from:ks.etrade@kotak.com subject:"Contract Note" has:attachment newer_than:2d'

def fetch_daily_contract_note(gmail_service):
    print("Checking for new Kotak contract notes...")
    save_directory = "downloads/kotak"
    
    return download_attachments(
        service=gmail_service, 
        query=KOTAK_SEARCH_QUERY, 
        save_dir=save_directory
    )

def extract_data_from_pdf(filepath):
    password = get_broker_password("kotak")
    if not password:
        return

    print(f"\n--- Processing: {filepath} ---")
    
    # Extract date from filename (e.g., CN_20260313_W8RHY_MER.pdf -> 2026-03-13)
    filename = os.path.basename(filepath)
    raw_date = filename.split('_')[1]
    trade_date = datetime.strptime(raw_date, '%Y%m%d').strftime('%Y-%m-%d')

    table_a_ledger = []
    table_b_spends = []
    
    total_stock_obligation = 0.0
    final_billed_amount = 0.0

    try:
        with pdfplumber.open(filepath, password=password) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                
                for table in tables:
                    for row in table:
                        clean_row = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                        
                        # --- 1. EXTRACT TABLE A (Stocks) ---
                        if clean_row and len(clean_row) > 13 and clean_row[0].startswith('IN'):
                            ISIN = clean_row[0]
                            security = clean_row[1]

                            # Extract Buy Data (Default to "0" if empty)
                            qty_buy = clean_row[2] if clean_row[2] else "0"
                            wap_buy = clean_row[3] if clean_row[3] else "0"
                            total_buy = clean_row[6] if clean_row[6] else "0"

                            # Extract Sell Data (Default to "0" if empty)
                            qty_sell = clean_row[7] if clean_row[7] else "0"
                            wap_sell = clean_row[8] if clean_row[8] else "0"
                            total_sell = clean_row[11] if clean_row[11] else "0"

                            # Determine WAP to display (Handles Intraday vs Single-direction trades)
                            if float(qty_buy) > 0 and float(qty_sell) > 0:
                                wap = f"B:{wap_buy} | S:{wap_sell}"
                            elif float(qty_buy) > 0:
                                wap = f"B:{wap_buy}"
                            else:
                                wap = f"S:{wap_sell}"

                            net_qty = int(clean_row[12])
                            net_obligation = float(clean_row[13].replace(',', ''))
                            
                            # Add to Table A
                            table_a_ledger.append({
                                "date": trade_date,
                                "ISIN": ISIN,
                                "security": security,
                                "net_quantity": net_qty,
                                "wap_before_brokerage": wap,
                                "net_obligation": net_obligation
                            })
                            
                            # Add to Table B (Stocks)
                            table_b_spends.append({
                                "date": trade_date,
                                "type": "stocks",
                                "symbol": security,
                                "price": net_obligation
                            })
                            
                            total_stock_obligation += net_obligation

                        # --- 2. EXTRACT FINAL BILLED AMOUNT ---
                        # Look for the debit/credit total to calculate exact taxes
                        if "Debit Total (Inclusive of all charges)" in clean_row:
                            # The amount is usually towards the end of the row
                            amounts = [col for col in clean_row if col.replace(',', '').replace('.', '').isdigit()]
                            if amounts:
                                final_billed_amount = float(amounts[-1].replace(',', ''))
                                # final_billed_amount += 0.01 # fixed brokerage

        # --- 3. CALCULATE TAXES FOR TABLE B ---
        if final_billed_amount > 0:
            # Total Taxes = Final Bill - Cost of Stocks
            total_taxes = round(final_billed_amount - total_stock_obligation, 2)
            
            table_b_spends.append({
                "date": trade_date,
                "type": "taxes and charges",
                "symbol": "",
                "price": total_taxes
            })

        # --- PRINT RESULTS ---
        print("\n--- TABLE A [Pure Ledger] ---")
        print(f"{'Date':<12} | {'Security':<20} | {'Qty':<5} | {'WAP':<8} | {'Obligation'}")
        print("-" * 65)
        for row in table_a_ledger:
            print(f"{row['date']:<12} | {row['security'][:20]:<20} | {row['net_quantity']:<5} | {row['wap_before_brokerage']:<8} | {row['net_obligation']}")

        print("\n--- TABLE B [Final Spends] ---")
        print(f"{'Date':<12} | {'Type':<18} | {'Symbol':<20} | {'Price'}")
        print("-" * 65)
        for row in table_b_spends:
            print(f"{row['date']:<12} | {row['type']:<18} | {row['symbol'][:20]:<20} | {row['price']}")

    except Exception as e:
        print(f"Failed to open or process {filepath}. Error: {e}")

def process_kotak(gmail_service):
    """Main workflow for Kotak"""
    #files = fetch_daily_contract_note(gmail_service)
    files = ['downloads/kotak/CN_20260309_W8RHY_MER.pdf', 'downloads/kotak/CN_20260310_W8RHY_MER.pdf', 'downloads/kotak/CN_20260311_W8RHY_MER.pdf', 'downloads/kotak/CN_20260312_W8RHY_MER.pdf', 'downloads/kotak/CN_20260313_W8RHY_MER.pdf']

    for file in files:
        extract_data_from_pdf(file)