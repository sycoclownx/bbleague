import csv
import os

def replace_ampersand(value):
    return value.replace("&", "and")

def process_csv_file(file_path):
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)

        # Create a new CSV file with the same name but with "_processed" appended
        processed_file_path = os.path.splitext(file_path)[0] + "_processed.csv"
        with open(processed_file_path, 'w', newline='') as processed_csvfile:
            writer = csv.writer(processed_csvfile)
            writer.writerow(headers)

            for row in reader:
                processed_row = [replace_ampersand(value) if isinstance(value, str) else value for value in row]
                writer.writerow(processed_row)

    print(f"Processed {file_path}")

# Replace this with the path to your directory
directory_path = "/opt/stacks/bbleague/teams"

for filename in os.listdir(directory_path):
    if filename.endswith(".csv"):
        file_path = os.path.join(directory_path, filename)
        process_csv_file(file_path)