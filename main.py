# main.py
from utils import connect_gmail
from modules.kotak import process_kotak

def main():
    print("Starting Daily Contract Note Reader...")
    
    try:
        gmail_service = connect_gmail()
        
        # Run broker modules
        process_kotak(gmail_service)
        
        print("Daily execution completed successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()