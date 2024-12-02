import csv
import os

def remove_quotes(value):
    return value.replace('"', '')

def process_csv_file(file_path):
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)

        # Create a new CSV file with the same name but with "_cleaned" appended
        cleaned_file_path = os.path.splitext(file_path)[0] + "_cleaned.csv"
        with open(cleaned_file_path, 'w', newline='') as cleaned_csvfile:
            writer = csv.writer(cleaned_csvfile)
            writer.writerow(headers)

            for row in reader:
                cleaned_row = [remove_quotes(value) for value in row]
                writer.writerow(cleaned_row)

    print(f"Processed {file_path}")

# Replace this with the path to your directory
directory_path = "/opt/stacks/bbleague/teams"

for filename in os.listdir(directory_path):
    if filename.endswith(".csv"):
        file_path = os.path.join(directory_path, filename)
        process_csv_file(file_path)