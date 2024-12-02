import os

# Replace this with the path to your directory
directory_path = "/opt/stacks/bbleague/teams"

# Get a list of all files in the directory
files = os.listdir(directory_path)

# First pass: Remove files that don't end with "_cleaned_processed.csv"
for file in files:
    if not file.endswith("_cleaned_processed.csv"):
        file_path = os.path.join(directory_path, file)
        os.remove(file_path)

# Second pass: Rename the remaining files by removing "_cleaned_processed" from the file name
for file in files:
    if file.endswith("_cleaned_processed.csv"):
        # Rename the file by removing "_cleaned_processed" from the file name
        new_file_name = file.replace("_cleaned_processed.csv", ".csv")
        file_path = os.path.join(directory_path, file)
        new_file_path = os.path.join(directory_path, new_file_name)

        # Check if the new file path exists before renaming
        if os.path.exists(new_file_path):
            print(f"File '{new_file_name}' already exists. Skipping rename.")
        else:
            try:
                os.rename(file_path, new_file_path)
            except FileNotFoundError:
                print(f"File '{file}' does not exist. Skipping rename.")

print("All excess files have been removed and the remaining files have been renamed.")