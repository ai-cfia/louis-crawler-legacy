import os
from collections import Counter

def count_extensions(directory):
    ext_counter = Counter()
    for root, dirs, files in os.walk(directory):
        for file in files:
            _, ext = os.path.splitext(file)
            ext_counter[ext.lower()] += 1
    return ext_counter

if __name__ == "__main__":
    directory = "./storage"  # Change this to your target directory
    counts = count_extensions(directory)
    for ext, count in counts.most_common():
        print(f"{ext or '[no extension]'}: {count}")