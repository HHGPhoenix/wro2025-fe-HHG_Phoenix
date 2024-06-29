import os
import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import paramiko
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
from threading import Thread, Event

# Configuration file
CONFIG_FILE = 'PC_Tools/sync_handler_data.json'
GITIGNORE_FILE = '.gitignore'
WATCHED_DIR = None
RPI_CONFIGS = {}

# Load or create configuration file
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# Load initial configuration
def load_initial_config():
    global GITIGNORE_FILE, WATCHED_DIR, RPI_CONFIGS
    config = load_config()
    
    WATCHED_DIR = config.get('WATCHED_DIR', None)
    if not WATCHED_DIR:
        print("No WATCHED_DIR specified in the config. Exiting.")
        sys.exit(1)
    
    GITIGNORE_FILE = os.path.join(WATCHED_DIR, '.gitignore')
    
    RPI_CONFIGS = config.get('RPIs', {})
    if not RPI_CONFIGS:
        print("No RPIs specified in the config. Exiting.")
        sys.exit(1)

# Update or add new RPI configuration dynamically
def configure_rpi(config):
    updated = False
    for rpi_host, rpi_details in RPI_CONFIGS.items():
        if rpi_details.get('status') == 'unconfigured':
            print(f"RPI {rpi_host} is unconfigured. Please configure it and rerun the script.")
            sys.exit(0)
        elif 'status' not in rpi_details:
            RPI_CONFIGS[rpi_host]['status'] = 'unconfigured'
            updated = True
            print(f"New RPI {rpi_host} detected. Added to configuration as unconfigured.")
    
    if updated:
        config['RPIs'] = RPI_CONFIGS
        save_config(config)
        sys.exit(0)
    
    print("All RPIs are configured.")
    return config

# Load initial configuration and ensure all RPIs are configured
config = load_initial_config()
config = configure_rpi(config)

print(f"Watching {WATCHED_DIR} for changes")

# Load .gitignore entries
def load_gitignore_entries():
    if os.path.exists(GITIGNORE_FILE):
        with open(GITIGNORE_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# Check if the file should be ignored
def is_ignored(file_path):
    gitignore_entries = load_gitignore_entries()
    for entry in gitignore_entries:
        if entry in file_path:
            return True
    return False

# SSH connection setup
def ssh_connect(rpi_host, rpi_user, rpi_pass, rpi_port):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(rpi_host, port=rpi_port, username=rpi_user, password=rpi_pass)
    return client

# Synchronize file to RPi
def sync_file_to_rpi(local_file, remote_file, rpi_details):
    if is_ignored(local_file):
        print(f"Ignoring {local_file} based on .gitignore rules")
        return
    
    client = ssh_connect(rpi_details['host'], rpi_details['user'], rpi_details['pass'], rpi_details['port'])
    sftp = client.open_sftp()
    # Ensure the remote directory exists
    remote_dir = os.path.dirname(remote_file)
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        # Create remote directory and all intermediate directories if they don't exist
        current_dir = ''
        for dir in remote_dir.split('/'):
            current_dir += dir + '/'
            try:
                sftp.stat(current_dir)
            except FileNotFoundError:
                sftp.mkdir(current_dir)
    sftp.put(local_file, remote_file)
    sftp.close()
    client.close()
    print(f"Synchronized {local_file} to {remote_file} on RPi {rpi_details['host']}")

# Event handler for directory monitoring
class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            local_path = event.src_path
            relative_path = os.path.relpath(local_path, WATCHED_DIR).replace("\\", "/")  # Replace backslashes with forward slashes
            for rpi, details in RPI_CONFIGS.items():
                remote_path = os.path.join(details['dest_dir'], relative_path).replace("\\", "/")
                sync_file_to_rpi(local_path, remote_path, details)

    def on_created(self, event):
        if not event.is_directory:
            local_path = event.src_path
            relative_path = os.path.relpath(local_path, WATCHED_DIR).replace("\\", "/")  # Replace backslashes with forward slashes
            for rpi, details in RPI_CONFIGS.items():
                remote_path = os.path.join(details['dest_dir'], relative_path).replace("\\", "/")
                sync_file_to_rpi(local_path, remote_path, details)

# Synchronize all files to RPIs
def sync_all_files_to_rpis():
    def sync_file(file_info):
        local_file_path, remote_file_path, rpi_details = file_info
        sync_file_to_rpi(local_file_path, remote_file_path, rpi_details)

    files_to_sync = []
    for root, dirs, files in os.walk(WATCHED_DIR):
        for file in files:
            local_file_path = os.path.join(root, file)
            if not is_ignored(local_file_path):
                relative_path = os.path.relpath(local_file_path, WATCHED_DIR).replace("\\", "/")
                for rpi, details in RPI_CONFIGS.items():
                    remote_file_path = os.path.join(details['dest_dir'], relative_path).replace("\\", "/")
                    files_to_sync.append((local_file_path, remote_file_path, details))

    # Use ThreadPoolExecutor to sync files in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(sync_file, files_to_sync)

# Monitor for new or updated RPI configurations
def monitor_rpi_configs(stop_event):
    def scan_for_rpis():
        # Placeholder: Replace this with your logic to scan for RPIs
        # This could be a network scan or reading from a known list
        detected_rpis = ["192.168.1.10", "192.168.1.11"]  # Example IPs
        return detected_rpis

    while not stop_event.is_set():
        detected_rpis = scan_for_rpis()
        config_changed = False

        for rpi in detected_rpis:
            if rpi not in RPI_CONFIGS:
                print(f"New RPI {rpi} detected. Adding to configuration.")
                RPI_CONFIGS[rpi] = {
                    'host': rpi,
                    'user': 'default_user',  # Replace with actual default or input mechanism
                    'pass': 'default_pass',  # Replace with actual default or input mechanism
                    'port': 22,  # Default SSH port
                    'dest_dir': '/path/to/dest',  # Default destination directory
                    'status': 'unconfigured'
                }
                config_changed = True

        if config_changed:
            config = load_config()
            config['RPIs'] = RPI_CONFIGS
            save_config(config)
            print("Configuration updated with new RPIs.")
        
        # Reload config to check for updates
        updated_config = load_config()
        if updated_config != config:
            print("Configuration file has been updated.")
            config.update(updated_config)
            RPI_CONFIGS.update(config.get('RPIs', {}))
        
        time.sleep(5)

# Modify the main function to call sync_all_files_to_rpis at the start and monitor RPIs
def main():
    if "--run-in-cmd" not in sys.argv:
        # Construct the command to run this script in a new cmd window
        cmd_command = f'cmd /c "{sys.executable}" "{sys.argv[0]}" --run-in-cmd'
        # Open a new cmd window and run this script with the special argument
        subprocess.Popen(cmd_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        # Original main functionality
        sync_all_files_to_rpis()
        
        stop_event = Event()
        
        # Start the configuration monitoring thread
        config_monitor_thread = Thread(target=monitor_rpi_configs, args=(stop_event,))
        config_monitor_thread.start()

        event_handler = ChangeHandler()
        observer = Observer()
        observer.schedule(event_handler, path=WATCHED_DIR, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            stop_event.set()
        observer.join()
        config_monitor_thread.join()

if __name__ == "__main__":
    main()
