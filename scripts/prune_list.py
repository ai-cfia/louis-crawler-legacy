import os
import json

# Set your top-level directory here
tld = "./"  # Change this to your actual path if needed
metadata_dir = os.path.join(tld, "metadata")
html_dir = os.path.join(tld, "html")
output_file = os.path.join(tld, "pruned_files.txt")

results = []

for filename in os.listdir(metadata_dir):
    if filename.endswith(".json"):
        json_path = os.path.join(metadata_dir, filename)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            url = data.get("url", "")
            if ".ca/fr" in url:
                results.append(f"html/{filename.replace('.json', '.html')}")
                results.append(f"metadata/{filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

with open(output_file, "w", encoding="utf-8") as out:
    for line in results:
        out.write(line + "\n")

print(f"Done. {len(results)//2} pairs written to {output_file}")
