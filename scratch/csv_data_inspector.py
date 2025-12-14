import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# Hardcoded Directories
INPUT_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Scripts\Input"
OUTPUT_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Scripts\Output"
PROCESSED_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Scripts\Processed"
LOGS_DIR = r"C:\Users\wsd3\OneDrive\Takoradi\Scripts\logs"


class CSVDataInspector:
    def __init__(self,
                 input_dir=INPUT_DIR,
                 output_dir=OUTPUT_DIR,
                 processed_dir=PROCESSED_DIR,
                 logs_dir=LOGS_DIR):
        """
        Initialize CSV data inspector with hardcoded directories
        """
        # Ensure all directories exist
        for dir_path in [input_dir, output_dir, processed_dir, logs_dir]:
            os.makedirs(dir_path, exist_ok=True)

        # Setup logging
        log_filename = os.path.join(logs_dir, f'data_inspection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_dir = processed_dir
        self.logs_dir = logs_dir

    def load_csv_files(self):
        """
        Load and merge all CSV files in the input directory

        :return: Merged DataFrame
        """
        # Find all CSV files
        csv_files = [
            os.path.join(self.input_dir, f)
            for f in os.listdir(self.input_dir)
            if f.lower().endswith('.csv')
        ]

        if not csv_files:
            raise ValueError("No CSV files found in input directory")

        # Read and merge files
        merged_df = pd.DataFrame()
        for file in csv_files:
            try:
                df = pd.read_csv(file, low_memory=False)
                merged_df = pd.concat([merged_df, df], ignore_index=True)
                self.logger.info(f"Loaded file: {file}")

                # Move processed file
                processed_file = os.path.join(
                    self.processed_dir,
                    os.path.basename(file)
                )
                os.rename(file, processed_file)
                self.logger.info(f"Moved to processed: {processed_file}")
            except Exception as e:
                self.logger.error(f"Could not process {file}: {e}")

        return merged_df

    def inspect_data_structure(self, df):
        """
        Perform initial data structure inspection

        :param df: Input DataFrame
        :return: Data structure insights
        """
        # Basic data structure analysis
        inspection_report = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': {}
        }

        for col in df.columns:
            col_info = {
                'dtype': str(df[col].dtype),
                'non_null_count': df[col].count(),
                'null_percentage': df[col].isnull().mean() * 100,
                'unique_values': df[col].nunique(),
                'sample_values': df[col].sample(min(5, len(df[col]))).tolist()
            }

            # Additional type-specific analysis
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info.update({
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean(),
                    'median': df[col].median()
                })
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                col_info.update({
                    'min_date': df[col].min(),
                    'max_date': df[col].max()
                })

            inspection_report['columns'][col] = col_info

        return inspection_report

    def generate_visualizations(self, df):
        """
        Generate basic visualizations for numeric and date columns

        :param df: Input DataFrame
        """
        # Create visualizations directory
        viz_dir = os.path.join(self.output_dir, 'visualizations')
        os.makedirs(viz_dir, exist_ok=True)

        # Numeric columns visualization
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        # Boxplot for numeric columns
        if not numeric_cols.empty:
            plt.figure(figsize=(15, 6))
            df[numeric_cols].boxplot()
            plt.title('Boxplot of Numeric Columns')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, 'numeric_boxplot.png'))
            plt.close()

        # Correlation heatmap
        if len(numeric_cols) > 1:
            plt.figure(figsize=(12, 10))
            correlation_matrix = df[numeric_cols].corr()
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
            plt.title('Correlation Heatmap of Numeric Columns')
            plt.tight_layout()
            plt.savefig(os.path.join(viz_dir, 'correlation_heatmap.png'))
            plt.close()

        # Date column analysis (if exists)
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if not date_cols.empty:
            for col in date_cols:
                plt.figure(figsize=(12, 6))
                df.groupby(pd.Grouper(key=col, freq='M')).size().plot(kind='line')
                plt.title(f'Monthly Trend for {col}')
                plt.xlabel('Date')
                plt.ylabel('Count')
                plt.tight_layout()
                plt.savefig(os.path.join(viz_dir, f'{col}_monthly_trend.png'))
                plt.close()

    def save_inspection_report(self, inspection_report):
        """
        Save inspection report to JSON

        :param inspection_report: Inspection insights
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = os.path.join(
            self.output_dir,
            f'data_inspection_report_{timestamp}.json'
        )

        # Save report
        import json
        with open(report_filename, 'w') as f:
            json.dump(inspection_report, f, indent=4, default=str)

        self.logger.info(f"Saved inspection report: {report_filename}")

    def process_and_inspect(self):
        """
        Main method to process and inspect CSV data

        :return: Processed DataFrame
        """
        # Load CSV files
        df = self.load_csv_files()

        # Inspect data structure
        inspection_report = self.inspect_data_structure(df)

        # Save inspection report
        self.save_inspection_report(inspection_report)

        # Generate visualizations
        self.generate_visualizations(df)

        # Save merged CSV
        merged_filename = os.path.join(
            self.output_dir,
            f'merged_imports_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        df.to_csv(merged_filename, index=False)
        self.logger.info(f"Saved merged dataset: {merged_filename}")

        return df


def main():
    try:
        inspector = CSVDataInspector()
        processed_df = inspector.process_and_inspect()

        # Print basic summary
        print("Data Inspection Complete!")
        print(f"Total Rows: {len(processed_df)}")
        print(f"Total Columns: {len(processed_df.columns)}")
        print("Inspection report and visualizations saved in:", OUTPUT_DIR)

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()