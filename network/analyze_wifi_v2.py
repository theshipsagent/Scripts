import os
import sys
from subprocess import check_output, SubprocessError, DEVNULL
import datetime
import socket
import requests
from scapy.all import ARP, Ether, srp

# --- Configuration ---
LOG_DIR = r"C:\Users\wsd3\OneDrive\GRoK\Projects\MANIFEST\Logs"
ANALYSIS_LOG = os.path.join(LOG_DIR, "analysis_log.txt")
ERROR_LOG = os.path.join(LOG_DIR, "error_log.txt")
TARGET_IP = "192.168.1.1/24"  # Change this to match your network subnet

# --- Ensure log directory exists ---
os.makedirs(LOG_DIR, exist_ok=True)

def log_to_file(path, message):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now()} - {message}\n")

def get_vendor(mac):
    try:
        response = requests.get(f"https://api.macvendors.com/{mac}", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except requests.RequestException:
        pass
    return "Unknown Vendor"

def scan_network(ip_range):
    try:
        arp = ARP(pdst=ip_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp
        result = srp(packet, timeout=3, verbose=0)[0]
        return [{
            "ip": rcv.psrc,
            "mac": rcv.hwsrc,
        } for sent, rcv in result]
    except Exception as e:
        log_to_file(ERROR_LOG, f"Error during scan: {e}")
        return []

def resolve_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return "Unknown"

def is_online(ip):
    try:
        output = check_output(["ping", "-n", "1", "-w", "500", ip], stderr=DEVNULL)
        return "TTL=" in output.decode("utf-8", errors="ignore")
    except SubprocessError:
        return False

def analyze_devices(devices):
    for device in devices:
        ip = device.get("ip")
        mac = device.get("mac")
        hostname = resolve_hostname(ip)
        online = is_online(ip)
        vendor = get_vendor(mac)

        log_msg = (
            f"IP: {ip}\n"
            f"MAC: {mac}\n"
            f"Vendor: {vendor}\n"
            f"Hostname: {hostname}\n"
            f"Online: {'Yes' if online else 'No'}\n"
            f"{'-'*40}"
        )
        log_to_file(ANALYSIS_LOG, log_msg)
        print(log_msg)

def main():
    try:
        print("🔍 Scanning the network...")
        devices = scan_network(TARGET_IP)
        print(f"✅ Found {len(devices)} device(s). Analyzing...")
        analyze_devices(devices)
    except Exception as e:
        log_to_file(ERROR_LOG, f"Fatal error: {e}")
        print("❌ Something went wrong. Check error log.")

if __name__ == "__main__":
    main()
