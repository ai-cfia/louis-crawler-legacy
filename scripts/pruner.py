import os
import json
import shutil

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

for fname in os.listdir(src_metadata):
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
print(f"Done. Processed files with substring '{substring}' from {src_metadata} to {dest_metadata} and {dest_html}.")
