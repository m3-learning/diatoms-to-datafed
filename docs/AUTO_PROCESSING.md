# Automated Data Processing

## Overview
The automated data processing feature monitors a directory called `new_data` for new scientific data files and automatically processes them using DataFed operations. This allows for a streamlined workflow where new data is automatically cataloged and transferred to the DataFed repository.

## How It Works

1. The system monitors a directory called `new_data` within your configured data path
2. When new files are detected, they're compared against a log file to see which ones haven't been processed yet
3. For each new file:
   - Metadata is extracted based on the file type (supported formats: h5, xrdml, dm4, ibw)
   - A DataFed record is created with the extracted metadata
   - The file is uploaded to DataFed using the dataPut command
   - The process is logged to prevent duplicate uploads

## Setup

1. Make sure your environment is properly configured with access to DataFed
2. Log in to the DataFed system through the UI
3. Select your desired context and collection where files should be stored
4. Navigate to the "Auto Processing" tab
5. Click "Start Auto Processing" to begin the automated workflow

## Monitoring Progress

The "Auto Processing" tab provides real-time information about the processing status:

- **Status**: Current state of the processing workflow
- **Current File**: The file currently being processed
- **Task ID**: The DataFed task ID for the current file operation
- **Progress**: Visual progress bar showing the overall task completion percentage

## Logs

The system maintains a log file (default: `backup_log.json`) that tracks:
- List of processed files to avoid duplicates
- Timestamps for when each file was processed

## Troubleshooting

If the automated processing stops or encounters errors:

1. Check the status message for specific error information
2. Verify that the `new_data` directory exists and is accessible
3. Ensure you have proper DataFed credentials and authorization
4. Check that the selected context and collection are valid
5. Stop and restart the automated processing

## Flow Diagram

```
new_data folder
    │
    ├── Check log file for processed files
    │
    ├── Find unprocessed files
    │   │
    │   ├── [No new files] ──► Wait and check again
    │   │
    │   └── [New files found]
    │       │
    │       ├── For each file:
    │       │   │
    │       │   ├── Extract metadata
    │       │   │
    │       │   ├── Create DataFed record (dataCreate)
    │       │   │
    │       │   ├── Upload file to DataFed (dataPut)
    │       │   │
    │       │   └── Update log file
    │       │
    │       └── Update progress in UI
    │
    └── Continue monitoring
``` 