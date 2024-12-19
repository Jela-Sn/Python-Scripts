import os
import re
import csv
from collections import defaultdict
import subprocess
import datetime

# Define directories and log file paths
HOME_DIR = os.path.expanduser("~")
ENGAGEMENT_DIR = os.path.join(HOME_DIR, "engagement")
HELPERS_DIR = os.path.join(ENGAGEMENT_DIR, "helpers")
LOGS_DIR = os.path.join(ENGAGEMENT_DIR, "logs")
NMAP_RESULTS_DIR = os.path.join(ENGAGEMENT_DIR, "nmap_results")

TODAY = datetime.date.today().strftime("%Y-%m-%d")
COMMAND_LOG = os.path.join(LOGS_DIR, f"command-log.{TODAY}.txt")
NOTES_LOG = os.path.join(LOGS_DIR, "notes-log.txt")
NMAP_TARGETS_LOG = os.path.join(LOGS_DIR, "nmap-targets.txt")
NMAP_SUMMARY_LOG = os.path.join(LOGS_DIR, "nmap-summary.csv")

def setup_directories():
    """
    Creates the engagement directory structure if it does not exist.
    """
    directories = [ENGAGEMENT_DIR, HELPERS_DIR, LOGS_DIR, NMAP_RESULTS_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print(f"Engagement directories created or already exist at {ENGAGEMENT_DIR}")

def log_command(command):
    """
    Logs the execution of a shell command, its output, and its runtime.
    """
    start_time = datetime.datetime.now().strftime("%H:%M:%S")
    with open(COMMAND_LOG, "a") as log_file:
        log_file.write(f"[[ Command Start ]] {start_time}\n")
        log_file.write(f"[[ Command Text ]] {command}\n\n")

        try:
            process = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            log_file.write(process.stdout)
        except Exception as e:
            log_file.write(f"Error: {e}\n")

        end_time = datetime.datetime.now().strftime("%H:%M:%S")
        log_file.write(f"\n[[ Command Ended ]] {end_time}\n")
        log_file.write("#" * 60 + "\n\n")

    print(f"Command logged to {COMMAND_LOG}")


def log_note(note):
    """
    Logs a time-stamped note to a log file.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(NOTES_LOG, "a") as log_file:
        log_file.write(f"{timestamp}: {note}\n")
        log_file.write("#" * 60 + "\n\n")
    print(f"Note saved to {NOTES_LOG}")


def find_nmap_targets(nmap_file, filter_port=None, filter_service=None):
    """
    Parses an Nmap scan result file to find open ports and services.
    Supports filtering by port or service and generates a summary.
    """
    if not os.path.exists(nmap_file):
        print(f"Error: File '{nmap_file}' not found.")
        return

    targets = []
    port_service_map = defaultdict(list)

    with open(nmap_file, "r") as file:
        for line in file:
            match = re.search(r"Discovered open port (\d+)/\w+ on (\d+\.\d+\.\d+\.\d+)", line)
            if match:
                port = match.group(1)
                ip = match.group(2)
                service = "unknown"

                # Check for service information in subsequent lines
                service_match = re.search(r"(\w+) \(\)", line)
                if service_match:
                    service = service_match.group(1)

                if filter_port and port != filter_port:
                    continue
                if filter_service and filter_service.lower() not in service.lower():
                    continue

                target = f"{ip}:{port}:{service}"
                targets.append(target)
                port_service_map[port].append(ip)

    unique_targets = sorted(set(targets))

    if unique_targets:
        with open(NMAP_TARGETS_LOG, "w") as log_file:
            log_file.write("\n".join(unique_targets))
        print(f"Found targets saved to {NMAP_TARGETS_LOG}")
        print("\n".join(unique_targets))
    else:
        print("No targets found with the specified filters.")

    # Generate a summary and save as CSV
    with open(NMAP_SUMMARY_LOG, "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Port", "Number of IPs", "IP List"])
        for port, ips in port_service_map.items():
            csv_writer.writerow([port, len(ips), ", ".join(ips)])
    print(f"Summary saved to {NMAP_SUMMARY_LOG}")


def main():
    """
    Main menu for logging commands, taking notes, or finding Nmap targets.
    """
    setup_directories()

    while True:
        print("\nChoose an option:")
        print("1) Log a command (alias: lc)")
        print("2) Add a note (alias: an)")
        print("3) Find Nmap targets (alias: fnt)")
        print("4) Exit (alias: exit)")

        choice = input("Enter your choice (1, 2, 3, 4, or alias): ").strip().lower()
        if choice in ("1", "lc"):
            command = input("Enter the command to run: ").strip()
            if command:
                log_command(command)
            else:
                print("Command cannot be empty.")
        elif choice in ("2", "an"):
            note = input("Enter your note: ").strip()
            if note:
                log_note(note)
            else:
                print("Note cannot be empty.")
        elif choice in ("3", "fnt"):
            nmap_file = input("Enter the path to the Nmap results file: ").strip()
            filter_port = input("Filter by port (leave empty for all): ").strip()
            filter_service = input("Filter by service (leave empty for all): ").strip()
            find_nmap_targets(nmap_file, filter_port or None, filter_service or None)
        elif choice in ("4", "exit"):
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or a valid alias.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExecution interrupted. Exiting...")