import psutil
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename='../system_performance.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Critical system processes to exclude from termination
CRITICAL_PROCESSES: set[str] = {
    'svchost.exe', 'csrss.exe', 'wininit.exe', 'winlogon.exe',
    'smss.exe', 'dwm.exe', 'explorer.exe', 'taskhostw.exe', 'conhost.exe'
}

# Updated CRITICAL_PROCESSES
CRITICAL_PROCESSES = {
    'svchost.exe', 'csrss.exe', 'wininit.exe', 'winlogon.exe',
    'smss.exe', 'dwm.exe', 'explorer.exe', 'taskhostw.exe', 'conhost.exe',
    'MemCompression'  # Added to exclude from termination
}

def get_process_info():
    """Collect process information sorted by memory usage."""
    processes = []
    for proc in psutil.process_iter(['name', 'memory_info', 'cpu_percent']):
        try:
            mem = proc.memory_info().rss / 1024 / 1024  # Memory in MB
            cpu = proc.cpu_percent(interval=0.1)
            processes.append({
                'name': proc.name(),
                'pid': proc.pid,
                'memory_mb': mem,
                'cpu_percent': cpu
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(processes, key=lambda x: x['memory_mb'], reverse=True)

def identify_non_essential_processes(processes, mem_threshold_mb=100):
    """Identify non-essential processes exceeding memory threshold."""
    non_essential = []
    for proc in processes:
        if (
            proc['memory_mb'] > mem_threshold_mb and
            proc['name'].lower() not in CRITICAL_PROCESSES and
            not proc['name'].lower().startswith('python') and
            not proc['name'].lower() in ['pycharm64.exe', 'zotero.exe']
        ):
            non_essential.append(proc)
    return non_essential

def terminate_process(pid):
    """Safely terminate a process by PID."""
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=3)
        logging.info(f"Terminated process {proc.name()} (PID: {pid})")
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
        logging.error(f"Failed to terminate process {pid}: {str(e)}")
        return False

def main():
    logging.info("Starting system performance analysis")
    print("Analyzing system performance...")

    # Collect system stats
    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    mem_used_mb = mem.used / 1024 / 1024
    mem_total_mb = mem.total / 1024 / 1024

    # Log system stats
    logging.info(f"CPU Usage: {cpu_usage}%")
    logging.info(f"Memory Used: {mem_used_mb:.2f} MB / {mem_total_mb:.2f} MB ({mem.percent}%)")

    # Get process information
    processes = get_process_info()
    print(f"\nTop 5 Memory-Consuming Processes:")
    for proc in processes[:5]:
        print(f"Name: {proc['name']}, PID: {proc['pid']}, Memory: {proc['memory_mb']:.2f} MB, CPU: {proc['cpu_percent']:.2f}%")

    # Identify non-essential processes
    non_essential = identify_non_essential_processes(processes)
    if non_essential:
        print("\nNon-Essential High-Memory Processes (candidates for termination):")
        for proc in non_essential:
            print(f"Name: {proc['name']}, PID: {proc['pid']}, Memory: {proc['memory_mb']:.2f} MB")
            user_input = input(f"Terminate {proc['name']} (PID: {proc['pid']})? (y/n): ").lower()
            if user_input == 'y':
                if terminate_process(proc['pid']):
                    print(f"Process {proc['name']} terminated.")
                else:
                    print(f"Failed to terminate {proc['name']}.")
    else:
        print("\nNo non-essential high-memory processes found.")

    # Check PyCharm/Zotero-specific usage
    pycharm_zotero = [p for p in processes if p['name'].lower() in ['pycharm64.exe', 'zotero.exe']]
    if pycharm_zotero:
        print("\nPyCharm/Zotero Usage:")
        for proc in pycharm_zotero:
            print(f"Name: {proc['name']}, Memory: {proc['memory_mb']:.2f} MB, CPU: {proc['cpu_percent']:.2f}%")

    logging.info("Performance analysis completed")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Script error: {str(e)}")
        print(f"An error occurred: {str(e)}")
