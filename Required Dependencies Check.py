# Required Dependencies Check
# This script checks if the necessary Python packages are installed for the network device analysis script.

import pkg_resources
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# List of required packages
required_packages = [
    'textblob',  # For input preprocessing as per instructions
    'pyspellchecker',  # For input preprocessing as per instructions
]

# Function to check installed packages
def check_dependencies():
    logging.info("Checking required Python packages.")
    missing = []
    for package in required_packages:
        try:
            pkg_resources.get_distribution(package)
            logging.debug(f"Package {package} is installed.")
        except pkg_resources.DistributionNotFound:
            missing.append(package)
            logging.warning(f"Package {package} is not installed.")
    return missing

# Main execution
logging.info("Starting dependency check.")
missing_packages = check_dependencies()

# Output in Markdown format
print("# Python Package Dependency Check")
if missing_packages:
    print("## Missing Packages")
    print("The following packages are required but not installed:")
    for pkg in missing_packages:
        print(f"- {pkg}")
    print("\nInstall missing packages using pip:")
    print("```bash")
    for pkg in missing_packages:
        print(f"pip install {pkg}")
    print("```")
else:
    print("All required packages are installed.")
logging.info("Dependency check completed.")