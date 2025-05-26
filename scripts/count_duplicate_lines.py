import sys
from collections import Counter

def count_duplicate_lines(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line.rstrip('\n') for line in f]
    counter = Counter(lines)
    duplicates = {line: count for line, count in counter.items() if count > 1}
    return duplicates

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python count_duplicate_lines.py <file.txt>")
        sys.exit(1)
    filepath = sys.argv[1]
    duplicates = count_duplicate_lines(filepath)
    if not duplicates:
        print("No duplicate lines found.")
    else:
        print("Duplicate lines and their counts:")
        for line, count in duplicates.items():
            print(f"{repr(line)}: {count}")
