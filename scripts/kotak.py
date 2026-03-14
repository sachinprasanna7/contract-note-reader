# scripts/kotak.py
from scripts.gmail_reader import download_attachments

# You'll need to adjust the email address and subject based on Kotak's actual emails
KOTAK_SEARCH_QUERY = 'from:backoffice@kotaksecurities.com subject:"Digitally Signed Contract Note" has:attachment newer_than:6d'

def fetch_daily_contract_note(gmail_service):
    print("Checking for new Kotak contract notes...")
    
    # Save them to a specific broker folder
    save_directory = "downloads/kotak"
    
    downloaded_files = download_attachments(
        service=gmail_service, 
        query=KOTAK_SEARCH_QUERY, 
        save_dir=save_directory
    )
    
    return downloaded_files

def extract_data_from_pdf(filepath):
    # TODO: We will build this out later using PyPDF2 or pdfplumber
    # Kotak PDFs usually require a password (often your PAN card in caps)
    print(f"Extraction logic will run here for: {filepath}")
    pass

def process_kotak(gmail_service):
    """Main workflow for Kotak"""
    files = fetch_daily_contract_note(gmail_service)
    for file in files:
        extract_data_from_pdf(file)