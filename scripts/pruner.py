import os
import json
import shutil
from tqdm import tqdm

# Set these variables as needed
tld = 'storage-guidance-en'  # e.g. 'storage-guidance-fr'
dest = 'storage-guidance-en-prune'  # e.g. 'storage-guidance-fr-prune'
substring = '.ca/en'  # The substring to filter URLs

src_metadata = os.path.join(tld, 'metadata')
src_html = os.path.join(tld, 'html')
dest_metadata = os.path.join(dest, 'metadata')
dest_html = os.path.join(dest, 'html')

os.makedirs(dest_metadata, exist_ok=True)
os.makedirs(dest_html, exist_ok=True)

metadata_files = [f for f in os.listdir(src_metadata) if f.endswith('.json')]

pruned_list_path = os.path.join(os.getcwd(), 'pruned_list.txt')
pruned_files = []

for fname in tqdm(metadata_files, desc="Processing files"):
    if not fname.endswith('.json'):
        continue
    json_path = os.path.join(src_metadata, fname)
    with open(json_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error reading {fname}: {e}")
            continue
    url = data.get('url', '')
    if substring in url:
        # Copy JSON
        shutil.copy2(json_path, os.path.join(dest_metadata, fname))
        # Copy HTML
        html_name = fname.replace('.json', '.html')
        html_path = os.path.join(src_html, html_name)
        if os.path.exists(html_path):
            shutil.copy2(html_path, os.path.join(dest_html, html_name))
        else:
            print(f"Warning: HTML file {html_name} not found for {fname}")
            raise FileNotFoundError(f"HTML file {html_name} not found for {fname}")
    else:
        pruned_files.append(fname)

# Write pruned filenames to pruned_list.txt
with open(pruned_list_path, 'w', encoding='utf-8') as f:
    for fname in pruned_files:
        f.write(fname + '\n')

print(f"Pruned files list written to {pruned_list_path}")
print(f"Done. Processed files with substring '{substring}' from {src_metadata} to {dest_metadata} and {dest_html}.")

# Count files in source and destination
src_count = len([f for f in os.listdir(src_metadata) if f.endswith('.json')])
dest_count = len([f for f in os.listdir(dest_metadata) if f.endswith('.json')])
print(f"Source metadata files: {src_count}")
print(f"Destination metadata files: {dest_count}")
