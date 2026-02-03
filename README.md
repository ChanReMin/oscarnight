# Oscar Night Voting System

A web-based voting application built with Python for organizing and managing voting events, designed for company or team recognition ceremonies.

## Overview

This application provides a platform for employees to participate in voting activities, with features for vote tracking, daily limits, and gender-based analytics. The system uses Excel files for data storage and management.

## Features

- Employee voting system with daily vote limits
- Real-time vote counting and tracking
- Employee profile management with avatars
- Gender-based analytics
- Data synchronization and recalculation utilities
- Vote management and updates

## Project Structure

```
oscarnight/
├── app.py              # Main Flask application
├── sync.py             # Data synchronization script
├── recal_votes.py      # Vote recalculation utility
├── update_id.py        # Employee ID update utility
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore configuration
└── data.xlsx          # Main data storage (not tracked in git)
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

3. Prepare your data file:
   - Create a `data.xlsx` file in the root directory
   - Follow the data structure format described below

## Data Structure

The application uses an Excel file (`data.xlsx`) with the following columns:

| Column Name | Type | Description |
|-------------|------|-------------|
| **STT** | Stribng | Sequence number, used for viewing only |
| **vnname** | String | Vietnamese name of the employee |
| **englishname** | String | English name of the employee |
| **avatar** | String | URL or file path to employee's avatar image |
| **employeeId** | String | Unique identifier for each employee |
| **dailyvote** | String | Number of votes the employee can cast per day |
| **votecount** | String | Total number of votes the employee has received |
| **gender** | String | Gender of the employee (e.g., "Male", "Female") |

### Example Data

| STT | vnname | englishname | avatar | employeeId | dailyvote | votecount | gender |
|-----|--------|-------------|--------|------------|-----------|-----------|--------|
| 1 | Nguyễn Văn A | John Nguyen | /avatars/john.jpg | EMP001 | 5 | 23 | 1 |
| 2 | Trần Thị B | Mary Tran | /avatars/mary.jpg | EMP002 | 5 | 18 | 0 |
| 3 | Lê Văn C | Chris Le | /avatars/chris.jpg | EMP003 | 5 | 31 | 1 |
Gender 1 is for Male, 0 is for Female
## Usage

### Running the Application

```bash
python app.py
```

The application will start a web server (typically on `http://localhost:5000`).

### Utility Scripts

#### Synchronize Data
```bash
python sync.py
```
Synchronizes data between different sources or formats.

#### Recalculate Votes
```bash
python recal_votes.py
```
Recalculates vote counts, useful after data cleanup or migration.

#### Update Employee IDs
```bash
python update_id.py
```
Updates or normalizes employee ID formats across the dataset.

## Configuration

The application configuration may be adjusted in `app.py`. Common configurations include:

- Server host and port
- Daily vote limits
- File paths for data storage
- Avatar storage location

## Data Management

### Important Notes

- The `data.xlsx` file is not tracked by git (listed in `.gitignore`)
- Always backup your data file before running utility scripts
- Vote counts are cumulative and track total votes received
- Daily vote limits control how many votes each employee can cast per day

### Vote Counting

- **votecount**: Tracks the total number of votes an employee has **received** from others
- **dailyvote**: Limits how many votes an employee can **give** to others per day

## Dependencies

The application requires Python 3.x and the following packages (see `requirements.txt`):

- Flask (for web framework)
- openpyxl or pandas (for Excel file handling)
- Additional dependencies as specified in requirements.txt
