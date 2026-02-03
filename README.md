# Oscar Night Voting System

A web-based voting application built with Python Flask for organizing and managing voting events, designed for company or team recognition ceremonies.

## Overview

This application provides a platform for employees to participate in voting activities, with features for vote tracking, daily limits, gender-based analytics, and Google Sheets synchronization. The system uses Excel files for data storage and JSON for vote history tracking.

## Features

- Employee voting system with daily vote limits
- Real-time vote counting and tracking
- Employee profile management with avatars
- Gender-based analytics
- Vote history tracking in JSON format
- Google Sheets bidirectional synchronization
- Time-based voting period restrictions
- Admin endpoints for vote management
- Data recalculation utilities
- Vote management and updates
- CORS enabled for cross-origin requests
- File locking for concurrent access safety

## Project Structure

```
oscarnight/
├── app.py                  # Main Flask application
├── sync.py                 # Google Sheets synchronization functions
├── recal_votes.py          # Vote recalculation utility
├── update_id.py            # Employee ID update utility
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (SHEET_ID)
├── .gitignore             # Git ignore configuration
├── data.xlsx              # Main data storage (not tracked in git)
├── vote_history.json      # Vote history log (not tracked in git)
├── locks/                 # Directory for file locks
│   ├── data.lock         # Lock file for data.xlsx
│   └── vote_history.lock # Lock file for vote_history.json
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ChanReMin/oscarnight.git
cd oscarnight
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create necessary directories:
```bash
mkdir -p locks templates
```

4. Set up environment variables:
```bash
# Create .env file
echo "SHEET_ID=your_google_sheet_id_here" > .env
```

5. Prepare your data file:
   - Create a `data.xlsx` file in the root directory
   - Follow the data structure format described below

## Data Structure

### Excel File (`data.xlsx`)

The application uses an Excel file with the following columns:

| Column Name | Type | Description |
|-------------|------|-------------|
| **STT** | String | Sequence number, used for viewing only |
| **vnname** | String | Vietnamese name of the employee |
| **englishname** | String | English name of the employee |
| **avatar** | String | URL or file path to employee's avatar image |
| **employeeId** | String | Unique identifier for each employee |
| **dailyvote** | String | Number of votes the employee can cast per day |
| **votecount** | String | Total number of votes the employee has received |
| **gender** | String | Gender of the employee (1 for Male, 0 for Female) |

### Example Data

| STT | vnname | englishname | avatar | employeeId | dailyvote | votecount | gender |
|-----|--------|-------------|--------|------------|-----------|-----------|--------|
| 1 | Nguyễn Văn A | John Nguyen | /avatars/john.jpg | EMP001 | 5 | 23 | 1 |
| 2 | Trần Thị B | Mary Tran | /avatars/mary.jpg | EMP002 | 5 | 18 | 0 |
| 3 | Lê Văn C | Chris Le | /avatars/chris.jpg | EMP003 | 5 | 31 | 1 |

**Note**: Gender codes: `1` = Male, `0` = Female

### Vote History File (`vote_history.json`)

The application logs all votes in a JSON file with the following structure:

```json
{
  "EMP001": [
    {
      "candidateId": "EMP002",
      "time": "2026-01-26T14:30:00+07:00",
      "votecount": 2
    },
    {
      "candidateId": "EMP003",
      "time": "2026-01-27T10:15:00+07:00",
      "votecount": 1
    }
  ],
  "EMP002": [
    {
      "candidateId": "EMP001",
      "time": "2026-01-26T15:00:00+07:00",
      "votecount": 3
    }
  ]
}
```

**Structure**:
- Top-level keys are voter employee IDs
- Each voter has an array of vote records
- Each vote record contains:
  - `candidateId`: ID of the employee who received the vote
  - `time`: ISO 8601 timestamp in Vietnam timezone (UTC+7)
  - `votecount`: Number of votes cast in this transaction

## API Endpoints

### Frontend & Health Check

#### `GET /`
- **Description**: Serves the main voting interface HTML page
- **Returns**: `templates/index.html`
- **Authentication**: Not required

#### `GET /health`
- **Description**: Health check endpoint with current Vietnam time
- **Returns**: 
  ```json
  {
    "status": "ok",
    "time_vn": "2026-02-03T14:30:00+07:00"
  }
  ```
- **Status Codes**: `200` - Success

### Authentication

#### `POST /api/login`
- **Description**: Authenticate employee and get their daily vote count
- **Request Body**:
  ```json
  {
    "employeeId": "EMP001"
  }
  ```
- **Success Response** (200):
  ```json
  {
    "success": true,
    "dailyVoteRemaining": 5
  }
  ```
- **Error Responses**:
  - `400` - Missing employee ID:
    ```json
    {
      "success": false,
      "message": "Employee ID required"
    }
    ```
  - `401` - Invalid employee ID:
    ```json
    {
      "success": false,
      "message": "Invalid Employee ID"
    }
    ```

### Candidate & Voting Operations

#### `GET /api/candidates`
- **Description**: Get list of all employees available for voting
- **Returns** (200):
  ```json
  [
    {
      "employeeId": "EMP001",
      "vnname": "Nguyễn Văn A",
      "englishname": "John Nguyen",
      "avatar": "/avatars/john.jpg",
      "gender": "1",
      "votecount": 23,
      "dailyvote": 5
    }
  ]
  ```
- **Notes**: 
  - List order can be randomized (currently commented out)
  - All numeric fields are converted to integers

#### `POST /api/vote`
- **Description**: Submit vote(s) for a candidate
- **Request Body**:
  ```json
  {
    "employeeId": "EMP001",
    "candidateId": "EMP002",
    "voteForCount": 2
  }
  ```
- **Success Response** (200):
  ```json
  {
    "success": true,
    "votesUsed": 2,
    "dailyVoteRemaining": 3
  }
  ```
- **Error Responses**:
  - `400` - Missing fields:
    ```json
    {
      "success": false,
      "message": "Missing fields"
    }
    ```
  - `400` - Self-voting:
    ```json
    {
      "success": false,
      "message": "Cannot vote for yourself"
    }
    ```
  - `400` - Invalid vote count:
    ```json
    {
      "success": false,
      "message": "Invalid vote count"
    }
    ```
  - `400` - Insufficient votes:
    ```json
    {
      "success": false,
      "message": "Not enough daily votes"
    }
    ```
  - `400` - Invalid employee:
    ```json
    {
      "success": false,
      "message": "Invalid employee"
    }
    ```
  - `403` - Outside voting period:
    ```json
    {
      "success": false,
      "message": "Ai cho mà vote nữa, ko có đâu nha hẹ hẹ"
    }
    ```

- **Voting Period**: 
  - Start: January 26, 2026 at 10:00 AM (UTC+7)
  - End: January 30, 2026 at 12:00 PM (UTC+7)

- **Business Logic**:
  1. Validates voting time period
  2. Checks if voter and candidate exist
  3. Prevents self-voting
  4. Validates vote count > 0
  5. Checks daily vote limit
  6. Decrements voter's `dailyvote`
  7. Increments candidate's `votecount`
  8. Logs vote to `vote_history.json`
  9. Saves changes to Excel file

### Vote History & Analytics

#### `GET /api/vote-history/<employee_id>`
- **Description**: Get voting history for a specific employee (who they voted for)
- **Parameters**: 
  - `employee_id` (path): Employee ID
- **Returns** (200):
  ```json
  {
    "success": true,
    "employeeId": "EMP001",
    "history": [
      {
        "candidateId": "EMP002",
        "time": "2026-01-26T14:30:00+07:00",
        "votecount": 2
      }
    ]
  }
  ```

#### `GET /api/votes-received/<employee_id>`
- **Description**: Get all votes received by a specific employee (who voted for them)
- **Parameters**: 
  - `employee_id` (path): Employee ID
- **Returns** (200):
  ```json
  {
    "success": true,
    "candidateId": "EMP002",
    "totalVotesReceived": 15,
    "voterCount": 8,
    "voters": [
      {
        "voterId": "EMP001",
        "time": "2026-01-27T10:15:00+07:00",
        "votecount": 2
      },
      {
        "voterId": "EMP003",
        "time": "2026-01-26T15:00:00+07:00",
        "votecount": 3
      }
    ]
  }
  ```
- **Notes**: Voters are sorted by time (most recent first)

### Administrative Endpoints

#### `POST /api/admin/update-name`
- **Description**: Update an employee's English name
- **Request Body**:
  ```json
  {
    "employeeId": "T0699",
    "newName": "John Doe"
  }
  ```
- **Success Response** (200):
  ```json
  {
    "success": true,
    "message": "Updated English name for T0699",
    "employeeId": "T0699",
    "oldName": "Jane Smith",
    "newName": "John Doe"
  }
  ```
- **Error Responses**:
  - `400` - Missing employee ID or name
  - `404` - Employee not found

#### `POST /api/admin/increase-vote`
- **Description**: Increase an employee's daily vote count
- **Request Body**:
  ```json
  {
    "employeeId": "T0699",
    "voteIncrease": 10
  }
  ```
- **Success Response** (200):
  ```json
  {
    "success": true,
    "message": "Increased vote count for T0699 by 10",
    "employeeId": "T0699",
    "olddailyvoteCount": 5,
    "newdailyvoteCount": 15,
    "voteIncrease": 10
  }
  ```
- **Error Responses**:
  - `400` - Missing employee ID
  - `400` - Invalid vote increase value
  - `400` - Vote increase must be positive
  - `404` - Employee not found

### Google Sheets Synchronization

#### `POST /api/sync/from-sheet`
- **Description**: Sync data FROM Google Sheets TO local Excel file
- **Environment Required**: `SHEET_ID` in `.env`
- **Success Response** (200):
  ```json
  {
    "success": true,
    "message": "Synced from Google Sheets"
  }
  ```
- **Error Response** (500):
  ```json
  {
    "success": false,
    "message": "Unexpected error: [error details]"
  }
  ```

#### `POST /api/sync/to-sheet`
- **Description**: Sync data FROM local Excel TO Google Sheets
- **Environment Required**: `SHEET_ID` in `.env`
- **Success Response** (200):
  ```json
  {
    "success": true,
    "message": "Synced 50 rows from Excel to Google Sheets",
    "rowCount": 50
  }
  ```
- **Error Response** (500):
  ```json
  {
    "success": false,
    "message": "Sync failed: [error details]"
  }
  ```

## File Descriptions

### Core Application Files

#### `app.py`
Main Flask application file containing all backend logic.

**Key Components**:

1. **Imports & Configuration**:
   - Flask web framework with CORS support
   - pandas for Excel manipulation
   - filelock for thread-safe file operations
   - pytz for Vietnam timezone handling
   - Custom sync functions from `sync.py`

2. **Constants**:
   - `DATA_FILE = "data.xlsx"` - Main employee database
   - `VOTE_HISTORY_FILE = "vote_history.json"` - Vote transaction log
   - `VN_TZ = "Asia/Ho_Chi_Minh"` - Vietnam timezone (UTC+7)
   - Lock files for concurrent access protection

3. **Helper Functions**:
   - `read_excel()`: Thread-safe Excel reading with FileLock
   - `write_excel(rows)`: Thread-safe Excel writing with FileLock
   - `find_employee(employee_id)`: Lookup employee by ID
   - `read_vote_history()`: Load vote history from JSON
   - `write_vote_history(history)`: Save vote history to JSON
   - `log_vote(voter_id, candidate_id, vote_count)`: Append vote to history

4. **Route Handlers**:
   - Frontend routes (`/`)
   - Authentication routes (`/api/login`)
   - Voting routes (`/api/vote`, `/api/candidates`)
   - History routes (`/api/vote-history`, `/api/votes-received`)
   - Admin routes (`/api/admin/*`)
   - Sync routes (`/api/sync/*`)
   - Health check (`/health`)

5. **Business Logic**:
   - Time-based voting restrictions (Jan 26-30, 2026)
   - Daily vote limit enforcement
   - Self-voting prevention
   - Concurrent access safety with file locking
   - Vote transaction logging

**Server Configuration**:
- Host: `0.0.0.0` (accessible from network)
- Port: `8000`

#### `sync.py`
Google Sheets synchronization utility.

**Functions**:
- `sync_to_sheet()`: Push local Excel data to Google Sheets
  - Reads from `data.xlsx`
  - Writes to Google Sheet specified by `SHEET_ID` environment variable
  - Overwrites sheet data completely
  
- `sync_from_sheet()`: Pull Google Sheets data to local Excel
  - Reads from Google Sheet specified by `SHEET_ID`
  - Writes to `data.xlsx`
  - Returns success/error status

**Requirements**:
- Google Sheets API credentials
- `SHEET_ID` environment variable in `.env`
- Appropriate Google Cloud project setup

**Usage**:
```bash
# Standalone sync to google sheet
python sync.py

# Or via API endpoints
curl -X POST http://localhost:8000/api/sync/to-sheet
curl -X POST http://localhost:8000/api/sync/from-sheet
```

#### `recal_votes.py`
Vote recalculation script that recounts all votes from history.

**Purpose**:
- Rebuilds `votecount` column from `vote_history.json`
- Fixes discrepancies between history and current counts
- Useful after data corruption or migration

**Process**:
1. Reads all vote records from `vote_history.json`
2. Aggregates votes by candidate ID
3. Updates `votecount` in `data.xlsx`
4. Preserves all other employee data

**When to Use**:
- After manual data edits
- After restoring from backup
- When vote counts seem incorrect
- After database migration

**Usage**:
```bash
python recal_votes.py
```

**Safety**:
- Uses file locking to prevent concurrent modifications
- Preserves original employee data
- Only updates `votecount` column

#### `update_id.py`
Employee ID update and normalization utility.

**Purpose**:
- Update employee IDs in bulk
- Normalize ID formats (e.g., add prefixes, change format)
- Migrate from old ID system to new one

**Typical Use Cases**:
- Standardizing ID format across organization
- Adding company prefix to IDs
- Migrating from numeric to alphanumeric IDs
- Fixing incorrectly entered IDs

**Usage**:
```bash
python update_id.py
```

#### `.env`
Environment variables configuration (not tracked in git).

**Required Variables**:
```bash
SHEET_ID=your_google_spreadsheet_id_here
```

**How to Get SHEET_ID**:
1. Open your Google Sheet
2. Look at the URL: `https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit`
3. Copy the `[SHEET_ID]` portion

## Usage

### Running the Application

```bash
# Standard run
python app.py

### Utility Scripts

#### Synchronize with Google Sheets
```bash
# Sync local data TO Google Sheets
curl -X POST http://localhost:8000/api/sync/to-sheet

# Sync FROM Google Sheets to local
curl -X POST http://localhost:8000/api/sync/from-sheet
```

#### Recalculate Votes
```bash
python recal_votes.py
```
Recalculates vote counts from `vote_history.json`, useful after:
- Data cleanup or migration
- Manual edits to vote history
- Restoring from backup

#### Update Employee IDs
```bash
python update_id.py
```
Updates or normalizes employee ID formats across the dataset.

## Configuration

### Application Settings (in `app.py`)

```python
# Server
HOST = "0.0.0.0"  # Accessible from network
PORT = 8000

# Timezone
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")  # UTC+7

# Voting Period
vote_start = VN_TZ.localize(datetime(2026, 1, 26, 10, 0, 0))  # Jan 26, 10:00 AM
vote_end = VN_TZ.localize(datetime(2026, 1, 30, 12, 0, 0))    # Jan 30, 12:00 PM

# Files
DATA_FILE = "data.xlsx"
VOTE_HISTORY_FILE = "vote_history.json"
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# Google Sheets ID for synchronization
SHEET_ID=1a2b3c4d5e6f7g8h9i0j_example_sheet_id
```

## Data Management

### Important Notes

- The `data.xlsx` file is not tracked by git (listed in `.gitignore`)
- The `vote_history.json` is not tracked by git
- Always backup both files before running utility scripts
- Vote counts are cumulative and track total votes received
- Daily vote limits control how many votes each employee can cast per day
- All file operations use `FileLock` for thread safety

### Vote Counting Logic

- **votecount**: Tracks the total number of votes an employee has **received** from others (read from `vote_history.json`)
- **dailyvote**: Tracks how many votes an employee can **still give** to others today (decremented with each vote cast)

### File Locking

The application uses `filelock` to ensure thread-safe access:
- `locks/data.lock` - Protects `data.xlsx`
- `locks/vote_history.lock` - Protects `vote_history.json`

### Backup Strategy

**Recommended Backup Schedule**:
1. Daily backup of `data.xlsx` and `vote_history.json`
2. Backup before running any utility scripts
3. Keep backups for at least 30 days
4. Sync to Google Sheets regularly as additional backup

**Backup Commands**:
```bash
# Manual backup
cp data.xlsx backups/data_$(date +%Y%m%d_%H%M%S).xlsx
cp vote_history.json backups/vote_history_$(date +%Y%m%d_%H%M%S).json

# Sync to cloud
curl -X POST http://localhost:8000/api/sync/to-sheet
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

## API Testing Examples

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"employeeId": "EMP001"}'

# Get candidates
curl http://localhost:8000/api/candidates

# Submit vote
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{
    "employeeId": "EMP001",
    "candidateId": "EMP002",
    "voteForCount": 2
  }'

# Get vote history
curl http://localhost:8000/api/vote-history/EMP001

# Get votes received
curl http://localhost:8000/api/votes-received/EMP002

# Admin: Update name
curl -X POST http://localhost:8000/api/admin/update-name \
  -H "Content-Type: application/json" \
  -d '{"employeeId": "T0699", "newName": "John Doe"}'

# Admin: Increase votes
curl -X POST http://localhost:8000/api/admin/increase-vote \
  -H "Content-Type: application/json" \
  -d '{"employeeId": "T0699", "voteIncrease": 10}'

# Sync to Google Sheets
curl -X POST http://localhost:8000/api/sync/to-sheet

# Sync from Google Sheets
curl -X POST http://localhost:8000/api/sync/from-sheet
```
