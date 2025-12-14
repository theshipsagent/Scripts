import pandas as pd
from tkinter import filedialog, Tk

# Hide the root Tk window
root = Tk()
root.withdraw()

try:
    # Select input CSV file via Windows Explorer dialog
    input_file = filedialog.askopenfilename(title="Select Input CSV File", filetypes=[("CSV Files", "*.csv")])
    if not input_file:
        raise ValueError("No input file selected.")

    # Read the CSV file (handle large files with low_memory=False if needed)
    df = pd.read_csv(input_file, low_memory=False)

    # Check if dataframe has at least 1000 rows
    if len(df) < 1000:
        raise ValueError("Input CSV has fewer than 1000 rows.")

    # Retrieve a random sample of 1000 rows
    sample_df = df.sample(n=1000, random_state=42)  # random_state for reproducibility

    # Select output file path and name via save dialog
    output_file = filedialog.asksaveasfilename(title="Save Sample CSV As", defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if not output_file:
        raise ValueError("No output file selected.")

    # Save the sample to the new file
    sample_df.to_csv(output_file, index=False)

except Exception as e:
    # Error handling: Print error message
    print(f"Error: {str(e)}")