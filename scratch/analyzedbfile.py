# Import necessary libraries
import os
import sqlite3
import pyodbc  # For Access or ODBC-compatible databases
import pandas as pd
import logging
from datetime import datetime

# Setup logging
def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), "Logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"db_analyzer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return log_file

# Analyze SQLite database
def analyze_sqlite(file_path):
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        result = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            result.append({'Table': table_name, 'Columns': len(columns), 'Column_Names': [col[1] for col in columns]})
        conn.close()
        return result
    except Exception as e:
        logging.error(f"SQLite analysis failed for {file_path}: {e}")
        return None

# Analyze Access database (requires Microsoft Access Database Engine)
def analyze_access(file_path):
    try:
        conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={file_path};"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        tables = [table.table_name for table in cursor.tables(tableType='TABLE')]
        result = []
        for table in tables:
            cursor.execute(f"SELECT * FROM [{table}]")
            columns = [col[0] for col in cursor.description]
            result.append({'Table': table, 'Columns': len(columns), 'Column_Names': columns})
        conn.close()
        return result
    except Exception as e:
        logging.error(f"Access analysis failed for {file_path}: {e}")
        return None

# Analyze CSV file
def analyze_csv(file_path):
    try:
        df = pd.read_csv(file_path, nrows=1)  # Read only first row for structure
        return [{'Table': os.path.basename(file_path), 'Columns': len(df.columns), 'Column_Names': df.columns.tolist()}]
    except Exception as e:
        logging.error(f"CSV analysis failed for {file_path}: {e}")
        return None

# Main function
def analyze_database():
    # Hardcoded file path
    file_path = r"C:\Users\wsd3\OneDrive\Desktop\files.db"
    if not os.path.exists(file_path):
        print("File not found. Exiting.")
        return

    # Setup logging
    log_file = setup_logging()
    print(f"Logging to: {log_file}")
    logging.info(f"Analyzing file: {file_path}")

    # Determine file type and analyze
    file_ext = os.path.splitext(file_path)[1].lower()
    result = None
    if file_ext == '.sqlite' or file_ext == '.db':
        result = analyze_sqlite(file_path)
    elif file_ext in ['.mdb', '.accdb']:
        result = analyze_access(file_path)
    elif file_ext == '.csv':
        result = analyze_csv(file_path)
    else:
        logging.error(f"Unsupported file extension: {file_ext}")
        print(f"Unsupported file type: {file_ext}. Try SQLite, Access, or CSV.")
        return

    # Output results
    if result:
        print("\nDatabase Structure:")
        for table in result:
            print(f"Table: {table['Table']}")
            print(f"Number of Columns: {table['Columns']}")
            print(f"Column Names: {', '.join(table['Column_Names'])}")
            print("-" * 50)
            logging.info(f"Table: {table['Table']}, Columns: {table['Columns']}, Column Names: {', '.join(table['Column_Names'])}")
    else:
        print("Analysis failed. Check logs for details.")

if __name__ == "__main__":
    analyze_database()