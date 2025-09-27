# Value Estimation - ROIC Analysis Tool

Educational app for analyzing Return on Invested Capital (ROIC) through factor sensitivity analysis.

## Overview

This project replicates and extends a financial model from Excel (`MODEL WYCENY TTSA 24.09 — kopia.xlsx`) to create an interactive educational tool for understanding how various business factors influence ROIC.

## Key Components

### 1. Data Extraction
- **Source**: Excel model sheet with financial calculations
- **Output**: Both calculated values and formulas exported to CSV
- **Key Range**: M3:M42 (financial analysis table) and M20:M30 (ROIC factors)

### 2. ROIC Factors (M20:M30)
- Baza wyliczeń w dniach (Calculation base in days)
- Wskaźnik rotacji należności (Accounts receivable turnover)
- Wskaźnik rotacji zapasów (Inventory turnover)
- Wskaźnik rotacji zobowiązań (Accounts payable turnover)
- Inne aktywa obrotowe% przychodów (Other current assets %)
- Fundusze specjalne (Special funds)
- Saldo należności (Accounts receivable balance)
- Stan zapasów (Inventory level)
- Stan RMK czynne (Active working capital)
- Stan zobowiązań handlowych (Trade payables)
- RMK bierne (Passive working capital)

### 3. Planned Features
- **Factor Grid**: Interactive exploration of how factors influence ROIC
- **Monte Carlo Simulation**: Generate thousands of factor combinations
- **Linear Regression**: Fit factors → ROIC relationship
- **Layman Interpretation**: Explain business impact in simple terms

## Usage

```bash
# Setup
uv sync

# Extract Excel data
uv run python scripts/convert_excel.py

# Run analysis (coming soon)
uv run streamlit run app.py
```

## Files

- `scripts/convert_excel.py` - Excel to CSV converter
- `data/` - Extracted values and formulas
- `app.py` - Streamlit educational interface (planned)
