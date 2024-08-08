#!/bin/bash

echo "Installing required packages..."
pip install -r requirements.txt

echo "Running NektoPSY bot..."
python main.py

read -p "Press any key to continue..."
