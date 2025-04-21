# Diatoms to DataFed

A service that automatically transfers microscope data to DataFed repository.

## Features

- Automatically detects new files in the microscope data directory
- Processes files daily at midnight
- Tracks processed files to avoid duplicates
- Uploads data to DataFed with metadata
- Comprehensive logging

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd diatoms-to-datafed
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## Configuration

1. Edit `config.yaml`:
   - Set `watch_directory` to your microscope data directory
   - Set `datafed.repo_id` to your DataFed repository ID
   - Adjust other settings as needed

2. Create the logs directory:
```bash
mkdir logs
```

## Usage

Run the service:
```bash
diatoms-to-datafed
```

The service will:
- Start running in the background
- Check for new files every day at midnight
- Process and upload new files to DataFed
- Log all activities to `logs/diatoms_to_datafed.log`
- Track processed files in `logs/processed_files.json`

## Logs

- Application logs: `logs/diatoms_to_datafed.log`
- Processed files log: `logs/processed_files.json`

## Requirements

- Python 3.9 or higher
- DataFed account and repository
- Access to the microscope data directory 