from pathlib import Path

# Define source and destination directory
source_dir = Path.home() / "Downloads"
destination_dir = Path('c:/Users/kidsa/OneDrive/Documents/Projects/mlops-projects/expense_dashboard/data/transactions')

# File mapping for static filenames
static_file_mapping = {
    "activity.csv": "amex_transactions.csv",
}

# String-based Chase file patterns
chase_patterns = {
    "Chase6708_Activity": "chase_checkings_transactions.csv",
    "Chase6031_Activity": "chase_savings_transactions.csv",
}

# Function to move and handle file overwrites
def move_file(source_file, destination_file):
    if destination_file.exists():
        destination_file.unlink()  # Delete the existing file before moving
    source_file.rename(destination_file)
    print(f"Moved: {source_file.name} → {destination_file.name}")
    
# Move static files
for original_name, new_name in static_file_mapping.items():
    source_file = source_dir / original_name
    destination_file = destination_dir / new_name

    if source_file.exists():
        move_file(source_file, destination_file)
    else:
        print(f"File not found: {original_name}")
        
# Move Chase files using string matching
for file in source_dir.iterdir():
    for pattern, new_name in chase_patterns.items():
        if pattern in file.name:  # Check if filename contains the pattern
            destination_file = destination_dir / new_name
            move_file(file, destination_file)
            print(f"Successfully moved {file.name} to {destination_file}")
            break  # Stop once the correct file is found

print("File processing complete!")