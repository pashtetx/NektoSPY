#!/bin/bash

echo "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing required packages..."
pip install -r requirements.txt

echo "Running NektoSPY bot..."
python main.py

read -p "Press any key to continue..."
