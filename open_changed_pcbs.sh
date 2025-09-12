#!/bin/bash

# Simple shell script to open all changed KiCad PCB files
# This is a quick alternative to the Python scripts

echo "=== Opening Changed KiCad PCB Files ==="
echo

# Get list of changed PCB files
changed_pcbs=$(git diff HEAD~10..HEAD --name-only | grep '\.kicad_pcb$')

if [ -z "$changed_pcbs" ]; then
    echo "No changed PCB files found."
    exit 0
fi

echo "Changed PCB files:"
echo "$changed_pcbs" | nl -v1 -s'. '
echo

# Count files
count=$(echo "$changed_pcbs" | wc -l)
echo "Found $count changed PCB files."

# Find KiCad PCB editor
if [ -f "/Applications/KiCad/KiCad.app/Contents/MacOS/pcbnew" ]; then
    KICAD_PATH="/Applications/KiCad/KiCad.app/Contents/MacOS/pcbnew"
elif command -v pcbnew &> /dev/null; then
    KICAD_PATH="pcbnew"
else
    echo "Error: Could not find KiCad PCB editor (pcbnew)"
    echo "Please ensure KiCad is installed and accessible."
    exit 1
fi

echo "Using KiCad at: $KICAD_PATH"
echo

# Ask for confirmation
read -p "Open all $count PCB files? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo "Opening PCB files..."

# Open each file
opened=0
while IFS= read -r pcb_file; do
    if [ -f "$pcb_file" ]; then
        echo "Opening: $pcb_file"
        "$KICAD_PATH" "$pcb_file" &
        ((opened++))
        sleep 1  # Small delay between opens
    else
        echo "Warning: File not found: $pcb_file"
    fi
done <<< "$changed_pcbs"

echo
echo "Successfully opened $opened PCB files."
echo "Each file should now be open in a separate KiCad window."
