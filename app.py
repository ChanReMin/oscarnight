from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import time
import threading
from datetime import datetime
import pytz
from filelock import FileLock
import pandas as pd
import random
import json

# Import sync functions from sync.py
from sync import sync_to_sheet, sync_from_sheet

# ======================
# Init
# ======================
load_dotenv()

app = Flask(__name__)
CORS(app)

DATA_FILE = "data.xlsx"
LOCK_FILE = "locks/data.lock"
VOTE_HISTORY_FILE = "vote_history.json"
VOTE_LOCK_FILE = "locks/vote_history.lock"
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
SHEET_ID = os.getenv("SHEET_ID")

# ======================
# Excel Helpers
# ======================
def read_excel():
    with FileLock(LOCK_FILE):
        df = pd.read_excel(DATA_FILE, engine='openpyxl')
        df = df.fillna("")
        return df.to_dict('records')

def write_excel(rows):
    with FileLock(LOCK_FILE):
        df = pd.DataFrame(rows)
        df.to_excel(DATA_FILE, index=False, engine='openpyxl')

def find_employee(employee_id):
    rows = read_excel()
    for r in rows:
        if str(r["employeeId"]) == str(employee_id):
            return r, rows
    return None, rows

# ======================
# Vote History Helpers
# ======================
def read_vote_history():
    """Read vote history from JSON file"""
    with FileLock(VOTE_LOCK_FILE):
        if not os.path.exists(VOTE_HISTORY_FILE):
            return {}
        
        try:
            with open(VOTE_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

def write_vote_history(history):
    """Write vote history to JSON file"""
    with FileLock(VOTE_LOCK_FILE):
        with open(VOTE_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
def log_vote(voter_id, candidate_id, vote_count):
    """Log a vote to the history file"""
    history = read_vote_history()
    
    # Get current time in Vietnam timezone
    current_time = datetime.now(VN_TZ).isoformat()
    
    # Initialize voter's history if not exists
    if voter_id not in history:
        history[voter_id] = []
    
    # Add vote record
    vote_record = {
        "candidateId": candidate_id,
        "time": current_time,
        "votecount": vote_count
    }
    
    history[voter_id].append(vote_record)
    
    # Save to file
    write_vote_history(history)
# ======================
# Routes
# ======================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/login", methods=["POST"])
def login():
    employee_id = request.json.get("employeeId", "").strip()
    if not employee_id:
        return jsonify({"success": False, "message": "Employee ID required"}), 400

    emp, _ = find_employee(employee_id)
    if not emp:
        return jsonify({"success": False, "message": "Invalid Employee ID"}), 401

    return jsonify({
        "success": True,
        "dailyVoteRemaining": int(emp["dailyvote"])
    })

@app.route("/api/candidates", methods=["GET"])
def candidates():
    rows = read_excel()
    candidate_list = [
        {
            "employeeId": str(r["employeeId"]),
            "vnname": r["vnname"],
            "englishname": r["englishname"],
            "avatar": r["avatar"],
            "gender": r["gender"],
            "votecount": int(r["votecount"]),
            "dailyvote": int(r["dailyvote"])
        } for r in rows
    ]
    
    # Randomize the order
    # random.shuffle(candidate_list)
    
    return jsonify(candidate_list)

@app.route("/api/vote", methods=["POST"])
def vote():
    # Check if voting is allowed based on time
    current_time = datetime.now(VN_TZ)
    
    # Voting period: 10am UTC+7 on 26/1/2026 to 12pm UTC+7 on 30/1/2026
    vote_start = VN_TZ.localize(datetime(2026, 1, 26, 10, 0, 0))
    vote_end = VN_TZ.localize(datetime(2026, 1, 30, 12, 0, 0))
    if current_time < vote_start:
        return jsonify({
            "success": False, 
            "message": "Ai cho mà vote nữa, ko có đâu nha hẹ hẹ"
        }), 403
    
    if current_time > vote_end:
        return jsonify({
            "success": False, 
            "message": "Ai cho mà vote nữa, ko có đâu nha hẹ hẹ"
        }), 403
    data = request.json
    voter_id = data.get("employeeId")
    candidate_id = data.get("candidateId")
    vote_count = int(data.get("voteForCount", 1))

    if not voter_id or not candidate_id:
        return jsonify({"success": False, "message": "Missing fields"}), 400
    if voter_id == candidate_id:
        return jsonify({"success": False, "message": "Cannot vote for yourself"}), 400
    if vote_count <= 0:
        return jsonify({"success": False, "message": "Invalid vote count"}), 400

    rows = read_excel()

    voter = None
    candidate = None

    for r in rows:
        if str(r["employeeId"]) == str(voter_id):
            voter = r
        if str(r["employeeId"]) == str(candidate_id):
            candidate = r

    if not voter or not candidate:
        return jsonify({"success": False, "message": "Invalid employee"}), 400

    if int(voter["dailyvote"]) < vote_count:
        return jsonify({"success": False, "message": "Not enough daily votes"}), 400

    voter["dailyvote"] = int(voter["dailyvote"]) - vote_count
    candidate["votecount"] = int(candidate["votecount"]) + vote_count

    write_excel(rows)

    log_vote(str(voter_id), str(candidate_id), vote_count)

    return jsonify({
        "success": True,
        "votesUsed": vote_count,
        "dailyVoteRemaining": int(voter["dailyvote"])
    })

@app.route("/api/vote-history/<employee_id>", methods=["GET"])
def get_vote_history(employee_id):
    """Get vote history for a specific employee"""
    history = read_vote_history()
    employee_history = history.get(employee_id, [])
    
    return jsonify({
        "success": True,
        "employeeId": employee_id,
        "history": employee_history
    })

@app.route("/api/votes-received/<employee_id>", methods=["GET"])
def get_votes_received(employee_id):
    """Get who voted for a specific employee (candidate)"""
    history = read_vote_history()
    
    voters = []
    total_votes = 0
    
    # Loop through all voters in history
    for voter_id, vote_records in history.items():
        # Check each vote record
        for vote in vote_records:
            if vote.get("candidateId") == employee_id:
                voters.append({
                    "voterId": voter_id,
                    "time": vote.get("time"),
                    "votecount": vote.get("votecount")
                })
                total_votes += vote.get("votecount", 0)
    
    # Sort by time (most recent first)
    voters.sort(key=lambda x: x["time"], reverse=True)
    
    return jsonify({
        "success": True,
        "candidateId": employee_id,
        "totalVotesReceived": total_votes,
        "voterCount": len(voters),
        "voters": voters
    })
@app.route("/api/admin/update-name", methods=["POST"])
def update_employee_name():
    """
    Update employee's English name
    POST /api/admin/update-name
    Body: {
        "employeeId": "T0699",
        "newName": "John Doe"
    }
    """
    data = request.json
    employee_id = data.get("employeeId", "").strip()
    new_name = data.get("newName", "").strip()

    if not employee_id:
        return jsonify({"success": False, "message": "Employee ID required"}), 400
    
    if not new_name:
        return jsonify({"success": False, "message": "New name required"}), 400

    rows = read_excel()
    employee_found = False

    for r in rows:
        if str(r["employeeId"]) == str(employee_id):
            old_name = r.get("englishname", "")
            r["englishname"] = new_name
            employee_found = True
            break

    if not employee_found:
        return jsonify({"success": False, "message": "Employee not found"}), 404

    # Save changes
    write_excel(rows)

    return jsonify({
        "success": True,
        "message": f"Updated English name for {employee_id}",
        "employeeId": employee_id,
        "oldName": old_name,
        "newName": new_name
    })
@app.route("/api/admin/increase-vote", methods=["POST"])
def increase_vote_count():
    """
    Increase employee's vote count
    POST /api/admin/increase-vote
    Body: {
        "employeeId": "T0699",
        "voteIncrease": 10
    }
    """
    data = request.json
    employee_id = data.get("employeeId", "").strip()
    vote_increase = data.get("voteIncrease", 0)

    if not employee_id:
        return jsonify({"success": False, "message": "Employee ID required"}), 400
    
    try:
        vote_increase = int(vote_increase)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid vote increase value"}), 400
    
    if vote_increase <= 0:
        return jsonify({"success": False, "message": "Vote increase must be positive"}), 400

    rows = read_excel()
    employee_found = False

    for r in rows:
        if str(r["employeeId"]) == str(employee_id):
            old_vote_count = int(r.get("dailyvote", 0))
            new_vote_count = old_vote_count + vote_increase
            r["dailyvote"] = new_vote_count
            employee_found = True
            break

    if not employee_found:
        return jsonify({"success": False, "message": "Employee not found"}), 404

    # Save changes
    write_excel(rows)

    return jsonify({
        "success": True,
        "message": f"Increased vote count for {employee_id} by {vote_increase}",
        "employeeId": employee_id,
        "olddailyvoteCount": old_vote_count,
        "newdailyvoteCount": new_vote_count,
        "voteIncrease": vote_increase
    })
@app.route("/api/sync/from-sheet", methods=["POST"])
def sync_from_sheet_endpoint():
    """
    Sync data FROM Google Sheets TO local Excel file
    POST /api/sync/from-sheet
    """
    try:
        result = sync_from_sheet()
        status_code = 200 if result["success"] else 500
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}"
        }), 500

@app.route("/api/sync/to-sheet", methods=["POST"])
def sync_to_sheet_endpoint():
    """
    Sync data FROM local Excel TO Google Sheets
    POST /api/sync/to-sheet
    """
    try:
        # Call the sync_to_sheet function from sync.py
        # It doesn't return anything, so we catch exceptions to determine success
        sync_to_sheet()
        
        # If no exception, it succeeded
        rows = read_excel()
        return jsonify({
            "success": True,
            "message": f"Synced {len(rows)} rows from Excel to Google Sheets",
            "rowCount": len(rows)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Sync failed: {str(e)}"
        }), 500

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "time_vn": datetime.now(VN_TZ).isoformat()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
