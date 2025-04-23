#!/usr/bin/env python
"""
Utility script to generate a configuration file from environment variables.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

# Load environment variables
load_dotenv()

from diatoms_to_datafed.config import load_config, save_config

def main():
    """Generate configuration from environment variables."""
    # Default output file
    output_file = Path("config.yaml")
    
    # Check if output file is provided as argument
    if len(sys.argv) > 1:
        output_file = Path(sys.argv[1])
    
    print(f"Generating configuration file at: {output_file}")
    
    # Load default configuration and apply environment variables
    config = load_config(Path("config.yaml"))
    
    # Save configuration
    save_config(config, output_file)
    
    print("Configuration file generated successfully.")
    print("The following environment variables were applied:")
    
    # Display applied environment variables
    import os
    env_prefixes = ["WATCH_", "LOG_", "DATAFED_"]
    for key in os.environ:
        for prefix in env_prefixes:
            if key.startswith(prefix):
                print(f"  {key}={os.environ[key]}")
                break
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 