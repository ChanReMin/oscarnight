import json
import os
from filelock import FileLock
import pandas as pd
from datetime import datetime
import pytz
from sync import sync_to_sheet, log

# Configuration
DATA_FILE = "data.xlsx"
LOCK_FILE = "locks/data.lock"
VOTE_HISTORY_FILE = "vote_history.json"
VOTE_LOCK_FILE = "locks/vote_history.lock"
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


def read_vote_history():
    """Read vote history from JSON file"""
    with FileLock(VOTE_LOCK_FILE):
        if not os.path.exists(VOTE_HISTORY_FILE):
            log("❌ Vote history file not found!")
            return {}
        
        try:
            with open(VOTE_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            log("❌ Error reading vote history file!")
            return {}


def read_excel():
    """Read Excel file with file lock"""
    with FileLock(LOCK_FILE):
        df = pd.read_excel(DATA_FILE, engine='openpyxl')
        df = df.fillna("")
        return df


def write_excel(df):
    """Write Excel file with file lock"""
    with FileLock(LOCK_FILE):
        df.to_excel(DATA_FILE, index=False, engine='openpyxl')


def recalculate_votes_from_history():
    """
    Recalculate vote counts from vote history and update Excel file
    """
    log("=" * 70)
    log("RECALCULATING VOTES FROM HISTORY")
    log("=" * 70)
    
    # Read vote history
    log("\n📖 Reading vote history...")
    history = read_vote_history()
    
    if not history:
        log("❌ No vote history found. Exiting...")
        return False
    
    log(f"✅ Found vote history for {len(history)} voters")
    
    # Calculate vote counts per candidate
    log("\n🔢 Calculating vote counts...")
    
    candidate_votes = {}
    total_vote_records = 0
    
    for voter_id, vote_records in history.items():
        for vote in vote_records:
            candidate_id = vote.get("candidateId")
            vote_count = vote.get("votecount", 0)
            
            if candidate_id:
                if candidate_id not in candidate_votes:
                    candidate_votes[candidate_id] = 0
                candidate_votes[candidate_id] += vote_count
                total_vote_records += 1
    
    log(f"✅ Processed {total_vote_records} vote records")
    log(f"✅ Found votes for {len(candidate_votes)} candidates")
    
    # Read Excel and update vote counts
    log("\n📝 Updating Excel file...")
    
    df = read_excel()
    
    if 'employeeId' not in df.columns or 'votecount' not in df.columns:
        log("❌ Required columns not found in Excel!")
        return False
    
    # Reset all vote counts to 0
    df['votecount'] = 0
    
    # Update vote counts based on history
    updated_count = 0
    
    for candidate_id, total_votes in candidate_votes.items():
        mask = df['employeeId'].astype(str) == str(candidate_id)
        
        if mask.any():
            df.loc[mask, 'votecount'] = total_votes
            updated_count += 1
    
    log(f"✅ Updated {updated_count} candidates")
    
    # Save to Excel
    log("\n💾 Saving to Excel...")
    write_excel(df)
    log(f"✅ Saved to {DATA_FILE}")
    
    # Sync to Google Sheets
    log("\n☁️ Syncing to Google Sheets...")
    try:
        sync_to_sheet()
        log("✅ Synced to Google Sheets!")
    except Exception as e:
        log(f"❌ Failed to sync: {str(e)}")
        return False
    
    log("\n" + "=" * 70)
    log("✅ RECALCULATION COMPLETED!")
    log("=" * 70)
    log(f"Total votes: {df['votecount'].sum()}")
    
    return True


if __name__ == "__main__":
    recalculate_votes_from_history()
