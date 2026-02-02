import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from filelock import FileLock
import os
import pandas as pd
import time
from datetime import datetime

load_dotenv()

DATA_FILE = "data.xlsx"
LOCK_FILE = "locks/data.lock"
SHEET_ID = os.getenv("SHEET_ID")
LOG_FILE = "logs/sync.log"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Initialize client globally so it can be reused
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    # Also write to log file
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def sync_to_sheet():
    try:
        ws = client.open_by_key(SHEET_ID).worksheet("Employees")
        
        # Get header row from Google Sheet to determine column order
        log("📋 Reading header row from Google Sheet...")
        time.sleep(0.3)  # Rate limit protection
        sheet_headers = ws.row_values(1)
        
        if not sheet_headers:
            log("❌ No headers found in Google Sheet row 1")
            raise ValueError("Google Sheet must have headers in row 1")
        
        log(f"📊 Google Sheet columns: {sheet_headers}")
        
        # Read Excel file
        with FileLock(LOCK_FILE):
            df = pd.read_excel(DATA_FILE, engine='openpyxl')
        
        log(f"📁 Excel file columns: {list(df.columns)}")
        
        # Check which columns exist in both Excel and Google Sheet
        excel_columns = set(df.columns)
        sheet_columns = set(sheet_headers)
        
        # Find missing columns
        missing_in_excel = sheet_columns - excel_columns
        missing_in_sheet = excel_columns - sheet_columns
        
        if missing_in_excel:
            log(f"⚠️ Warning: Columns in Sheet but not in Excel: {missing_in_excel}")
        
        if missing_in_sheet:
            log(f"⚠️ Warning: Columns in Excel but not in Sheet: {missing_in_sheet}")
        
        # Only use columns that exist in both
        valid_columns = [col for col in sheet_headers if col in excel_columns]
        
        if not valid_columns:
            log("❌ No matching columns found between Excel and Google Sheet")
            raise ValueError("No matching columns found")
        
        log(f"✅ Matching columns to sync: {valid_columns}")
        
        # Reorder DataFrame to match Google Sheet column order
        df_ordered = df[valid_columns].copy()
        
        # Add empty columns for any missing columns in Excel (to maintain Sheet structure)
        for col in sheet_headers:
            if col not in valid_columns:
                df_ordered[col] = ""
        
        # Reorder to exactly match sheet headers
        df_ordered = df_ordered[sheet_headers]
        
        # Clean the dataframe
        df_ordered = df_ordered.fillna("")
        df_ordered = df_ordered.replace([float('inf'), float('-inf')], "")
        
        # Convert everything to strings to be JSON-safe
        values = []
        for _, row in df_ordered.iterrows():
            values.append([str(val) if val != "" else "" for val in row])
        
        # Rate limit: sleep to ensure we don't exceed quota
        time.sleep(0.5)  # Add small delay before API call
        
        # Update starting from A2 (preserving headers in row 1)
        ws.update(values=values, range_name="A2")
        
        log(f"✅ Synced {len(df_ordered)} rows × {len(sheet_headers)} columns from Excel to Google Sheets")
        log(f"📊 Column order: {sheet_headers}")
        
    except gspread.exceptions.APIError as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "Quota exceeded" in str(e):
            log(f"⚠️ Rate limit hit, will retry next cycle: {e}")
        else:
            log(f"❌ API Error: {e}")
            raise
    except FileNotFoundError as e:
        log(f"❌ File not found: {e}")
        raise
    except Exception as e:
        log(f"❌ Sync failed: {e}")
        raise

if __name__ == "__main__":
    sync_to_sheet()


def sync_from_sheet():
    """Pull data from Google Sheets and save to Excel"""
    try:
        ws = client.open_by_key(SHEET_ID).worksheet("Employees")
        
        log("📥 Syncing FROM Google Sheet TO Excel...")
        time.sleep(0.3)  # Rate limit protection
        
        # Get all values from sheet
        all_values = ws.get_all_values()
        
        if len(all_values) < 2:
            log("⚠️ No data in sheet (only headers or empty)")
            return {"success": False, "message": "No data in sheet"}
        
        # First row is headers
        headers = all_values[0]
        data_rows = all_values[1:]
        
        log(f"📊 Sheet has {len(headers)} columns: {headers}")
        log(f"📊 Found {len(data_rows)} data rows")
        
        # Convert to list of dicts
        rows = []
        for row in data_rows:
            row_dict = {}
            for i, header in enumerate(headers):
                row_dict[header] = row[i] if i < len(row) else ""
            rows.append(row_dict)
        
        # Write to Excel with FileLock
        with FileLock(LOCK_FILE):
            df = pd.DataFrame(rows)
            df.to_excel(DATA_FILE, index=False, engine='openpyxl')
        
        log(f"✅ Synced {len(rows)} rows from Google Sheets to Excel")
        
        return {
            "success": True,
            "message": f"Synced {len(rows)} rows from Google Sheets to Excel",
            "rowCount": len(rows)
        }
        
    except gspread.exceptions.APIError as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "Quota exceeded" in str(e):
            log(f"⚠️ Rate limit hit: {e}")
        else:
            log(f"❌ API Error: {e}")
        return {
            "success": False,
            "message": f"API Error: {str(e)}"
        }
    except Exception as e:
        log(f"❌ Sync from sheet failed: {e}")
        return {
            "success": False,
            "message": f"Sync failed: {str(e)}"
        }
