import os
import re

def has_pdf_link(filepath):
    pdf_link_pattern = re.compile(r'https?://[^\s\"]+\.pdf', re.IGNORECASE)
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if pdf_link_pattern.search(line):
                    return True
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return False

def count_files_with_pdf_links(directory):
    count = 0
    total = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                total += 1
                filepath = os.path.join(root, file)
                if has_pdf_link(filepath):
                    count += 1
    return count, total

if __name__ == "__main__":
    directory = "./storage"  # Change if needed
    count, total = count_files_with_pdf_links(directory)
    print(f"{count} out of {total} text files contain at least one .pdf link.")
