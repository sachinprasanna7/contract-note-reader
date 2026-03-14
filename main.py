# main.py
from scripts.gmail_reader import connect_gmail
from scripts.kotak import process_kotak
def main():
    print("Starting Daily Contract Note Reader...")
    
    try:
        # Initialize Gmail API once
        gmail_service = connect_gmail()
        
        # Process Kotak
        process_kotak(gmail_service)
        
        print("Daily execution completed successfully.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()