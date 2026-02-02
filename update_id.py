import pandas as pd
import json
from filelock import FileLock
import os
from datetime import datetime

# File paths
MAPPING_FILE = "employee_mapping.json"
DATA_FILE = "data.xlsx"
LOCK_FILE = "locks/data.lock"
BACKUP_FILE = f"data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

def read_mapping():
    """Read the employee mapping from JSON file"""
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping_list = json.load(f)
        
        # Convert list of dicts to a simple dict for easy lookup
        # Key: old employeeId, Value: new FinalID
        mapping_dict = {}
        for item in mapping_list:
            old_id = str(item.get("employeeId", "")).strip()
            new_id = str(item.get("FinalID", "")).strip()
            if old_id and new_id:
                mapping_dict[old_id] = new_id
        
        return mapping_dict
    except FileNotFoundError:
        print(f"Error: {MAPPING_FILE} not found!")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {MAPPING_FILE}: {e}")
        return {}

def update_employee_ids():
    """Update employeeId in data.xlsx using mapping from employee_mapping.json"""
    
    # Read the mapping
    mapping = read_mapping()
    if not mapping:
        print("No mapping data found. Exiting.")
        return
    
    print(f"Loaded {len(mapping)} employee ID mappings")
    print("\nSample mappings:")
    for i, (old_id, new_id) in enumerate(list(mapping.items())[:5]):
        print(f"  {old_id} -> {new_id}")
    print()
    
    # Create locks directory if it doesn't exist
    os.makedirs("locks", exist_ok=True)
    
    try:
        # Use file lock to prevent concurrent access
        with FileLock(LOCK_FILE, timeout=10):
            # Read the Excel file
            print(f"Reading {DATA_FILE}...")
            df = pd.read_excel(DATA_FILE, engine='openpyxl')
            
            # Create backup
            print(f"Creating backup: {BACKUP_FILE}...")
            df.to_excel(BACKUP_FILE, index=False, engine='openpyxl')
            
            # Check if employeeId column exists
            if 'employeeId' not in df.columns:
                print(f"Error: 'employeeId' column not found in {DATA_FILE}")
                print(f"Available columns: {list(df.columns)}")
                return
            
            # Track updates
            updated_count = 0
            not_found_count = 0
            not_found_ids = []
            
            # Update employeeId values
            print(f"\nUpdating employee IDs...")
            for index, row in df.iterrows():
                old_id = str(row['employeeId']).strip()
                
                if old_id in mapping:
                    new_id = mapping[old_id]
                    df.at[index, 'employeeId'] = new_id
                    updated_count += 1
                    print(f"  Row {index + 1}: {old_id} -> {new_id}")
                else:
                    not_found_count += 1
                    not_found_ids.append(old_id)
            
            # Save updated Excel file
            print(f"\nSaving updated data to {DATA_FILE}...")
            df.to_excel(DATA_FILE, index=False, engine='openpyxl')
            
            # Print summary
            print("\n" + "="*60)
            print("UPDATE SUMMARY")
            print("="*60)
            print(f"Total rows in Excel: {len(df)}")
            print(f"Successfully updated: {updated_count}")
            print(f"Not found in mapping: {not_found_count}")
            
            if not_found_ids:
                print(f"\nEmployee IDs not found in mapping:")
                for emp_id in not_found_ids[:10]:  # Show first 10
                    print(f"  - {emp_id}")
                if len(not_found_ids) > 10:
                    print(f"  ... and {len(not_found_ids) - 10} more")
            
            print(f"\nBackup saved to: {BACKUP_FILE}")
            print("Update completed successfully!")
            
    except FileNotFoundError:
        print(f"Error: {DATA_FILE} not found!")
    except Exception as e:
        print(f"Error during update: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("="*60)
    print("EMPLOYEE ID UPDATE SCRIPT")
    print("="*60)
    print()
    
    # Confirm before proceeding
    response = input("This will update employeeId values in data.xlsx. Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        update_employee_ids()
    else:
        print("Update cancelled.")
