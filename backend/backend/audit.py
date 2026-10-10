import csv
import sys
from collections import Counter

filepath = r"C:\Users\samar\OneDrive\Desktop\HACKMATRIX\data\v2\FinMultiverse_100k_refined_training_dataset.csv"

try:
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        row_count = 0
        missing_counts = {col: 0 for col in header}
        unique_ids = set()
        duplicate_ids = 0
        labels = Counter()
        
        # Sample min/max tracking
        income_min = float('inf')
        income_max = float('-inf')
        
        for row in reader:
            row_count += 1
            if len(row) != len(header):
                continue
                
            record_id = row[0]
            if record_id in unique_ids:
                duplicate_ids += 1
            unique_ids.add(record_id)
            
            for i, val in enumerate(row):
                if not val.strip():
                    missing_counts[header[i]] += 1
            
            try:
                income = float(row[4])
                if income < income_min: income_min = income
                if income > income_max: income_max = income
            except ValueError:
                pass
                
            labels[row[-1]] += 1
            
    print(f"Row count: {row_count}")
    print(f"Column count: {len(header)}")
    print(f"Columns: {header}")
    print(f"Missing values: { {k:v for k,v in missing_counts.items() if v > 0} }")
    print(f"Duplicate IDs: {duplicate_ids}")
    print(f"Target distribution: {dict(labels)}")
    print(f"Monthly Income range: min={income_min}, max={income_max}")

except Exception as e:
    print(f"Error: {e}")
