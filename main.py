# main.py
from utils import connect_gmail, cleanup_downloads
from modules.kotak import process_kotak
from modules.angelone import process_angelone


def main():
    print("Starting Daily Contract Note Reader...")
    
    try:
        gmail_service = connect_gmail()
        
        # Run broker modules
        #process_kotak(gmail_service)
        #process_angelone(gmail_service)

        cleanup_downloads() # Optional: Clear downloads after processing
        
        print("Daily execution completed successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()