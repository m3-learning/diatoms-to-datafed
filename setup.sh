#!/bin/bash

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Install package
echo "Installing package..."
pip install -e .

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Configure DataFed
echo "Please configure DataFed:"
read -p "Enter your DataFed repository ID: " repo_id
read -p "Enter the path to your microscope data directory: " data_dir

# Update config.yaml
echo "Updating configuration..."
sed -i "s|watch_directory: .*|watch_directory: \"$data_dir\"|" config.yaml
sed -i "s|repo_id: .*|repo_id: \"$repo_id\"|" config.yaml

# Create systemd service
echo "Creating systemd service..."
sed -i "s|User=.*|User=$USER|" diatoms-to-datafed.service
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$(pwd)|" diatoms-to-datafed.service
sed -i "s|Environment=.*|Environment=\"PATH=$(pwd)/venv/bin\"|" diatoms-to-datafed.service
sed -i "s|ExecStart=.*|ExecStart=$(pwd)/venv/bin/diatoms-to-datafed|" diatoms-to-datafed.service

# Install service
echo "Installing systemd service..."
sudo cp diatoms-to-datafed.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable diatoms-to-datafed.service

echo "Setup complete! You can start the service with:"
echo "sudo systemctl start diatoms-to-datafed.service" 