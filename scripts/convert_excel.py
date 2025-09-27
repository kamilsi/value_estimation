#!/usr/bin/env python3
"""
Convert Excel model sheet to CSV files with both values and formulas.
"""
from pathlib import Path
import pandas as pd
import openpyxl

# Configuration
EXCEL_PATH = Path('MODEL WYCENY TTSA 24.09 — kopia.xlsx')
SHEET_NAME = 'model '
OUTPUT_DIR = Path('data')

def main():
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Reading Excel file: {EXCEL_PATH}")
    
    # Load values (calculated results)
    print("Extracting calculated values...")
    df_values = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine='openpyxl', header=None)
    
    # Load formulas using openpyxl
    print("Extracting formulas...")
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=False, read_only=False)
    ws = wb[SHEET_NAME]
    
    # Extract all formulas
    max_row = ws.max_row
    max_col = ws.max_column
    
    formulas = []
    for r in range(1, max_row + 1):
        row = []
        for c in range(1, max_col + 1):
            cell = ws.cell(row=r, column=c)
            if cell.data_type == 'f' and isinstance(cell.value, str):
                # Formula cell - add '=' prefix
                row.append('=' + cell.value)
            else:
                # Value cell
                row.append(cell.value)
        formulas.append(row)
    
    df_formulas = pd.DataFrame(formulas)
    
    # Save complete sheets
    print("Saving complete sheets...")
    df_values.to_csv(OUTPUT_DIR / 'model_values.csv', header=False, index=False)
    df_formulas.to_csv(OUTPUT_DIR / 'model_formulas.csv', header=False, index=False)
    
    # Try to save as parquet (may fail with mixed data types)
    try:
        print("Saving as parquet...")
        df_values.to_parquet(OUTPUT_DIR / 'model_values.parquet', index=False)
        df_formulas.to_parquet(OUTPUT_DIR / 'model_formulas.parquet', index=False)
        print("✅ Parquet files saved successfully")
    except Exception as e:
        print(f"⚠️  Parquet conversion failed (mixed data types): {e}")
        print("   CSV files are still available for analysis")
    
    # Extract specific ranges of interest
    print("Extracting specific ranges...")
    
    # M3:M42 (columns L=11, M=12 in 0-indexed)
    L3_M42_values = df_values.iloc[2:42, 11:13]
    L3_M42_formulas = df_formulas.iloc[2:42, 11:13]
    
    # J3:N42 (columns J=9, K=10, L=11, M=12, N=13 in 0-indexed)
    J3_N42_values = df_values.iloc[2:42, 9:14]
    J3_N42_formulas = df_formulas.iloc[2:42, 9:14]
    
    # M20:M30 (factors for ROIC analysis)
    L20_M30_values = df_values.iloc[19:30, 11:13]
    L20_M30_formulas = df_formulas.iloc[19:30, 11:13]
    
    # Save ranges
    L3_M42_values.to_csv(OUTPUT_DIR / 'L3_M42_values.csv', header=False, index=False)
    L3_M42_formulas.to_csv(OUTPUT_DIR / 'L3_M42_formulas.csv', header=False, index=False)
    
    J3_N42_values.to_csv(OUTPUT_DIR / 'J3_N42_values.csv', header=False, index=False)
    J3_N42_formulas.to_csv(OUTPUT_DIR / 'J3_N42_formulas.csv', header=False, index=False)
    
    L20_M30_values.to_csv(OUTPUT_DIR / 'L20_M30_values.csv', header=False, index=False)
    L20_M30_formulas.to_csv(OUTPUT_DIR / 'L20_M30_formulas.csv', header=False, index=False)
    
    print(f"✅ Conversion complete!")
    print(f"📁 Output directory: {OUTPUT_DIR.resolve()}")
    print(f"📊 Files created:")
    print(f"   - model_values.csv (complete sheet values)")
    print(f"   - model_formulas.csv (complete sheet formulas)")
    print(f"   - L3_M42_values.csv (M3:M42 values)")
    print(f"   - L3_M42_formulas.csv (M3:M42 formulas)")
    print(f"   - J3_N42_values.csv (J3:N42 values)")
    print(f"   - J3_N42_formulas.csv (J3:N42 formulas)")
    print(f"   - L20_M30_values.csv (M20:M30 values)")
    print(f"   - L20_M30_formulas.csv (M20:M30 formulas)")
    print(f"   - *.parquet files (same data in parquet format)")

if __name__ == "__main__":
    main()
