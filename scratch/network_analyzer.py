import subprocess
import re
import platform
import socket
import logging
import sys
import os
from datetime import datetime

# Set up logging to file and console
log_file = f"network_analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Function to check Python environment
def check_python_environment():
    logging.info("Checking Python environment.")
    try:
        python_version = subprocess.check_output([sys.executable, "--version"]).decode("utf-8", errors='ignore')
        logging.debug(f"Python version: {python_version.strip()}")
        return True
    except Exception as e:
        logging.error(f"Python environment check failed: {str(e)}")
        return False

# Function to get local IP and subnet
def get_local_subnet():
    logging.info("Retrieving local subnet information.")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        subnet = '.'.join(local_ip.split('.')[:3]) + '.'
        logging.debug(f"Local IP: {local_ip}, Subnet: {subnet}")
        return subnet, local_ip
    except Exception as e:
        logging.error(f"Failed to get local subnet: {str(e)}")
        return None, None

# Function to populate ARP table by pinging subnet
def populate_arp_table(subnet):
    logging.info(f"Attempting to populate ARP table by pinging subnet: {subnet}")
    try:
        # Ping a range of IPs to populate ARP table (1-254)
        for i in range(1, 255):
            ip = f"{subnet}{i}"
            try:
                subprocess.check_output(["ping", "-n", "1", "-w", "100", ip], stderr=subprocess.DEVNULL)
                logging.debug(f"Pinged {ip}")
            except subprocess.CalledProcessError:
                pass  # Ignore ping failures
    except Exception as e:
        logging.warning(f"Error during ARP table population: {str(e)}")

# Function to execute ARP command
def get_arp_table():
    logging.info("Executing ARP command.")
    os_type = platform.system().lower()
    if os_type != "windows":
        logging.error("This script is designed for Windows only.")
        return None
    try:
        result = subprocess.check_output(["arp", "-a"]).decode("utf-8", errors='ignore')
        logging.debug(f"ARP output retrieved. Length: {len(result)} characters")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"ARP command failed with return code {e.returncode}: {e.output.decode('utf-8', errors='ignore')}")
    except Exception as e:
        logging.error(f"Error executing ARP command: {str(e)}")
    return None

# Parse ARP output to extract IP, MAC, and type
def parse_arp_output(arp_output, subnet):
    logging.info("Parsing ARP output.")
    devices = []
    if arp_output:
        lines = arp_output.splitlines()
        logging.debug(f"Processing {len(lines)} lines from ARP output.")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F:-]{2}[-:][0-9a-fA-F:-]{2}[-:][0-9a-fA-F:-]{2}[-:][0-9a-fA-F:-]{2}[-:][0-9a-fA-F:-]{2}[-:][0-9a-fA-F:-]{2})\s+(\w+)", line)
            if match:
                ip = match.group(1)
                mac = match.group(2).upper().replace('-', ':')
                arp_type = match.group(3)
                if subnet and ip.startswith(subnet):
                    devices.append({"IP": ip, "MAC": mac, "Type": arp_type})
                    logging.debug(f"Found device: IP={ip}, MAC={mac}, Type={arp_type}")
    if not devices:
        logging.warning("No devices found in ARP output.")
    return devices

# Function to perform basic network diagnostics
def network_diagnostics():
    logging.info("Running network diagnostics.")
    diagnostics = []
    try:
        # Check network adapter status
        result = subprocess.check_output(["ipconfig"]).decode("utf-8", errors='ignore')
        diagnostics.append("## Network Adapter Status")
        diagnostics.append("```\n" + result + "\n```")
        logging.debug("Retrieved ipconfig output.")
    except Exception as e:
        logging.error(f"Error running ipconfig: {str(e)}")
        diagnostics.append("## Network Adapter Status\nError retrieving ipconfig data.")
    return diagnostics

# Main execution
logging.info("Starting network analyzer script.")
output_lines = ["# Network Device Analysis", f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]

# Check Python environment
if not check_python_environment():
    output_lines.append("## Error")
    output_lines.append("Python environment is not properly configured.")
    output_lines.append("Please ensure Python is installed and added to PATH.")
    output_lines.append("Run in PowerShell: `python --version` to verify.")
else:
    # Get local subnet
    subnet, local_ip = get_local_subnet()
    if subnet is None:
        output_lines.append("## Error")
        output_lines.append("Unable to retrieve local subnet information. Check logs for details.")
        logging.error("Script stopped due to subnet retrieval failure.")
    else:
        output_lines.append(f"Local IP: {local_ip}")
        output_lines.append(f"Subnet: {subnet}0/24")

        # Populate ARP table
        populate_arp_table(subnet)

        # Get and parse ARP table
        arp_output = get_arp_table()
        if arp_output is None:
            output_lines.append("## Error")
            output_lines.append("Unable to retrieve ARP table. Check logs for details.")
            logging.error("Script stopped due to ARP table retrieval failure.")
        else:
            devices = parse_arp_output(arp_output, subnet)
            if devices:
                output_lines.append("## Connected Devices")
                output_lines.append("| IP Address | MAC Address | Type |")
                output_lines.append("|------------|-------------|------|")
                for device in devices:
                    output_lines.append(f"| {device['IP']} | {device['MAC']} | {device['Type']} |")
                logging.info(f"Found {len(devices)} devices.")
            else:
                output_lines.append("## No Devices Found")
                output_lines.append("No devices detected or parsing error. Check logs for details.")
                logging.warning("No devices found or parsing error occurred.")

        # Run network diagnostics
        output_lines.extend(network_diagnostics())

# Save output to file
output_file = f"network_analyzer_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
try:
    with open(output_file, 'w') as f:
        for line in output_lines:
            f.write(line + '\n')
    logging.info(f"Output saved to {output_file}")
    output_lines.append(f"\nOutput saved to: {output_file}")
except Exception as e:
    logging.error(f"Failed to save output to file: {str(e)}")
    output_lines.append(f"\n## Error\nFailed to save output to {output_file}. Check logs for details.")

# Print output to console
for line in output_lines:
    print(line)

logging.info("Script execution completed.")

# Pause to keep console open
input("Press Enter to exit...")