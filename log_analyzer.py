#!/usr/bin/env python3
"""
Log analyzer for parallel crawler logs.
Helps analyze logs by task ID for debugging purposes.
"""

import re
import sys
from collections import defaultdict
from datetime import datetime


def parse_log_file(log_file):
    """Parse the log file and organize entries by task ID."""
    task_logs = defaultdict(list)
    general_logs = []

    # Regex to extract task ID from log lines
    task_pattern = r"\[TASK:([a-f0-9]{8})\]"

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                # Check if line contains a task ID
                task_match = re.search(task_pattern, line)
                if task_match:
                    task_id = task_match.group(1)
                    task_logs[task_id].append((line_num, line))
                else:
                    general_logs.append((line_num, line))

    except FileNotFoundError:
        print(f"Error: Log file '{log_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading log file: {e}")
        sys.exit(1)

    return task_logs, general_logs


def analyze_task_performance(task_logs):
    """Analyze performance metrics for each task."""
    task_stats = {}

    for task_id, logs in task_logs.items():
        stats = {
            "url": None,
            "start_time": None,
            "end_time": None,
            "duration": None,
            "status": "unknown",
            "error": None,
            "log_count": len(logs),
        }

        for line_num, log_line in logs:
            # Extract URL
            if "Processing URL" in log_line and stats["url"] is None:
                url_match = re.search(r"Processing URL.*?: (.+)", log_line)
                if url_match:
                    stats["url"] = url_match.group(1)

            # Extract timestamps
            timestamp_match = re.match(
                r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})", log_line
            )
            if timestamp_match:
                timestamp_str = timestamp_match.group(1)
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                    if stats["start_time"] is None:
                        stats["start_time"] = timestamp
                    stats["end_time"] = timestamp
                except ValueError:
                    pass

            # Determine status
            if "Successfully processed" in log_line:
                stats["status"] = "success"
            elif "Error processing" in log_line or "Failed to load" in log_line:
                stats["status"] = "error"
                # Try to extract error message
                if "Error processing" in log_line:
                    error_match = re.search(r"Error processing.*?: (.+)", log_line)
                    if error_match:
                        stats["error"] = error_match.group(1)

        # Calculate duration
        if stats["start_time"] and stats["end_time"]:
            duration = stats["end_time"] - stats["start_time"]
            stats["duration"] = duration.total_seconds()

        task_stats[task_id] = stats

    return task_stats


def print_task_summary(task_stats):
    """Print a summary of all tasks."""
    print("\n" + "=" * 80)
    print("TASK SUMMARY")
    print("=" * 80)
    print(f"{'Task ID':<10} {'Status':<10} {'Duration':<10} {'URL':<50}")
    print("-" * 80)

    for task_id, stats in task_stats.items():
        duration_str = f"{stats['duration']:.2f}s" if stats["duration"] else "N/A"
        url_short = (
            (stats["url"][:47] + "...")
            if stats["url"] and len(stats["url"]) > 50
            else (stats["url"] or "N/A")
        )
        print(f"{task_id:<10} {stats['status']:<10} {duration_str:<10} {url_short:<50}")


def print_task_details(task_id, logs):
    """Print detailed logs for a specific task."""
    print(f"\n" + "=" * 80)
    print(f"TASK DETAILS: {task_id}")
    print("=" * 80)

    for line_num, log_line in logs:
        print(f"{line_num:4d}: {log_line}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python log_analyzer.py <log_file> [task_id]")
        print("  log_file: Path to the crawler log file")
        print("  task_id:  Optional specific task ID to analyze (8 characters)")
        sys.exit(1)

    log_file = sys.argv[1]
    specific_task = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Analyzing log file: {log_file}")

    # Parse the log file
    task_logs, general_logs = parse_log_file(log_file)

    print(f"Found {len(task_logs)} tasks and {len(general_logs)} general log entries")

    if specific_task:
        # Show details for specific task
        if specific_task in task_logs:
            print_task_details(specific_task, task_logs[specific_task])
        else:
            print(f"Task ID '{specific_task}' not found in logs.")
            print(f"Available task IDs: {', '.join(sorted(task_logs.keys()))}")
    else:
        # Show summary of all tasks
        task_stats = analyze_task_performance(task_logs)
        print_task_summary(task_stats)

        # Show some general statistics
        successful_tasks = sum(
            1 for stats in task_stats.values() if stats["status"] == "success"
        )
        failed_tasks = sum(
            1 for stats in task_stats.values() if stats["status"] == "error"
        )

        print(f"\nSTATISTICS:")
        print(f"  Total tasks: {len(task_stats)}")
        print(f"  Successful: {successful_tasks}")
        print(f"  Failed: {failed_tasks}")
        print(f"  Unknown status: {len(task_stats) - successful_tasks - failed_tasks}")

        if task_stats:
            durations = [
                stats["duration"] for stats in task_stats.values() if stats["duration"]
            ]
            if durations:
                avg_duration = sum(durations) / len(durations)
                print(f"  Average duration: {avg_duration:.2f}s")
                print(f"  Min duration: {min(durations):.2f}s")
                print(f"  Max duration: {max(durations):.2f}s")


if __name__ == "__main__":
    main()
