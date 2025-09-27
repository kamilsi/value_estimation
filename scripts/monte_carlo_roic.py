#!/usr/bin/env python3
"""
Monte Carlo simulation for ROIC analysis.
Simulates 10,000 scenarios and performs linear regression analysis.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from pathlib import Path
import logging
try:
    from tqdm.auto import tqdm
except Exception:
    def tqdm(iterable, **kwargs):
        return iterable

logger = logging.getLogger(__name__)

def run_monte_carlo_simulation(n_simulations=10000):
    """
    Run Monte Carlo simulation for ROIC analysis.
    
    Args:
        n_simulations (int): Number of simulations to run
        
    Returns:
        pd.DataFrame: Results of all simulations
    """
    
    logger.info(f"Starting Monte Carlo simulation with {n_simulations:,} iterations...")
    
    # Define variable ranges based on Excel data analysis
    # These are the 6 key factors that affect ROIC through N32
    variable_ranges = {
        'N25_Fundusze_specjalne': (0.427529, 0.539533),
        'N26_Saldo_naleznosci': (81.939078, 131.111651),
        'N27_Stan_zapasow': (0.260255, 1.949483),
        'N28_Stan_RMK_czynne': (11.816190, 23.092303),
        'N29_Stan_zobowiazan_handlowych': (38.723212, 87.564628),
        'N30_RMK_bierne': (2.408775, 3.768109)
    }
    
    # Fixed values from Excel (these don't change in simulation)
    N6_przychody_produkty = 343.97001245999996
    N7_przychody_towary = 12.62342926
    N38_inny_kapital = 6.47708855
    N18_EBIT_margin = 0.08814386338232291
    N11_tax_rate = 0.14907783424850402
    
    logger.debug("Variable ranges:")
    for var, (min_val, max_val) in variable_ranges.items():
        logger.debug(f"  {var}: [{min_val:.6f}, {max_val:.6f}]")
    
    # Initialize results storage
    results = []
    
    logger.info("Running simulations...")
    
    for i in tqdm(range(n_simulations), desc="Simulating", unit="sim"):
        
        # Sample from uniform distribution for each variable
        sampled_values = {}
        for var, (min_val, max_val) in variable_ranges.items():
            sampled_values[var] = np.random.uniform(min_val, max_val)
        
        # Calculate N32 (Working Capital) using the formula: N26+N27+N28-N25-N29-N30
        N32_working_capital = (
            sampled_values['N26_Saldo_naleznosci'] +
            sampled_values['N27_Stan_zapasow'] +
            sampled_values['N28_Stan_RMK_czynne'] -
            sampled_values['N25_Fundusze_specjalne'] -
            sampled_values['N29_Stan_zobowiazan_handlowych'] -
            sampled_values['N30_RMK_bierne']
        )
        
        # Calculate N40 (Sales/Capital ratio)
        total_revenue = N6_przychody_produkty + N7_przychody_towary
        total_capital = N32_working_capital + N38_inny_kapital
        N40_sales_capital_ratio = total_revenue / total_capital if total_capital > 0 else 0
        
        # Calculate ROIC using the formula: N40 * N18 * (1 - N11)
        ROIC = N40_sales_capital_ratio * N18_EBIT_margin * (1 - N11_tax_rate)
        
        # Store results
        result = {
            'simulation_id': i + 1,
            'ROIC': ROIC,
            'N40_sales_capital_ratio': N40_sales_capital_ratio,
            'N32_working_capital': N32_working_capital,
            'total_revenue': total_revenue,
            'total_capital': total_capital,
            **sampled_values
        }
        results.append(result)
    
    # Convert to DataFrame
    df_results = pd.DataFrame(results)
    
    logger.info("Simulation completed")
    return df_results

def analyze_results(df_results):
    """
    Analyze simulation results and perform linear regression.
    
    Args:
        df_results (pd.DataFrame): Results from Monte Carlo simulation
    """
    
    logger.info("SIMULATION SUMMARY")
    logger.debug("=" * 50)
    
    # Basic statistics
    logger.info(f"Total simulations: {len(df_results):,}")
    logger.debug("ROIC statistics:")
    logger.debug(f"  Mean: {df_results['ROIC'].mean():.6f}")
    logger.debug(f"  Std:  {df_results['ROIC'].std():.6f}")
    logger.debug(f"  Min:  {df_results['ROIC'].min():.6f}")
    logger.debug(f"  Max:  {df_results['ROIC'].max():.6f}")
    logger.debug(f"  25th percentile: {df_results['ROIC'].quantile(0.25):.6f}")
    logger.debug(f"  75th percentile: {df_results['ROIC'].quantile(0.75):.6f}")
    
    # Variable statistics
    logger.debug("Variable means:")
    factor_vars = [col for col in df_results.columns if col.startswith(('N25_', 'N26_', 'N27_', 'N28_', 'N29_', 'N30_'))]
    for var in factor_vars:
        logger.debug(f"  {var}: {df_results[var].mean():.6f}")
    
    # Linear regression analysis
    logger.info("LINEAR REGRESSION ANALYSIS")
    logger.debug("=" * 50)
    
    # Prepare data for regression
    X = df_results[factor_vars].values
    y = df_results['ROIC'].values
    
    # Fit linear regression
    reg = LinearRegression()
    reg.fit(X, y)
    
    # Calculate R²
    y_pred = reg.predict(X)
    r2 = r2_score(y, y_pred)
    
    logger.info(f"R² Score: {r2:.6f}")
    logger.debug(f"Adjusted R²: {1 - (1 - r2) * (len(y) - 1) / (len(y) - X.shape[1] - 1):.6f}")
    
    # Standardized betas (standaryzowane)
    std_y = df_results['ROIC'].std()
    std_X = df_results[factor_vars].std()
    standardized_betas = []
    for j, var in enumerate(factor_vars):
        if std_y == 0 or std_X[var] == 0 or pd.isna(std_y) or pd.isna(std_X[var]):
            standardized_betas.append(np.nan)
        else:
            standardized_betas.append(reg.coef_[j] * (std_X[var] / std_y))

    # Regression coefficients
    logger.debug("Regression coefficients:")
    logger.debug(f"  Intercept: {reg.intercept_:.6f}")
    for var, raw_coef, beta_coef in zip(factor_vars, reg.coef_, standardized_betas):
        beta_str = "nan" if np.isnan(beta_coef) else f"{beta_coef:.6f}"
        logger.debug(f"  {var}: raw={raw_coef:.6f}, beta={beta_str}")
    
    # Create regression results table
    regression_table = pd.DataFrame({
        'Variable': factor_vars,
        'Coefficient': reg.coef_,
        'Standardized_Beta': standardized_betas,
        'Abs_Coefficient': np.abs(reg.coef_),
        'Abs_Standardized_Beta': np.abs(standardized_betas)
    }).sort_values('Abs_Standardized_Beta', ascending=False)
    
    logger.debug("REGRESSION COEFFICIENTS (sorted by importance):")
    logger.debug("\n" + regression_table.to_string(index=False, float_format='%.6f'))
    
    return regression_table

def save_results(df_results, regression_table):
    """
    Save results to CSV files.
    
    Args:
        df_results (pd.DataFrame): Simulation results
        regression_table (pd.DataFrame): Regression analysis results
    """
    
    output_dir = Path('data')
    output_dir.mkdir(exist_ok=True)
    
    # Save simulation results
    results_file = output_dir / 'monte_carlo_results.csv'
    df_results.to_csv(results_file, index=False)
    logger.info(f"Results saved to: {results_file}")
    
    # Save regression table
    regression_file = output_dir / 'regression_analysis.csv'
    regression_table.to_csv(regression_file, index=False)
    logger.info(f"Regression analysis saved to: {regression_file}")
    
    # Save summary statistics
    summary_stats = {
        'metric': ['n_simulations', 'roic_mean', 'roic_std', 'roic_min', 'roic_max', 'r2_score'],
        'value': [
            len(df_results),
            df_results['ROIC'].mean(),
            df_results['ROIC'].std(),
            df_results['ROIC'].min(),
            df_results['ROIC'].max(),
            r2_score(df_results['ROIC'], LinearRegression().fit(df_results[[col for col in df_results.columns if col.startswith(('N25_', 'N26_', 'N27_', 'N28_', 'N29_', 'N30_'))]].values, df_results['ROIC'].values).predict(df_results[[col for col in df_results.columns if col.startswith(('N25_', 'N26_', 'N27_', 'N28_', 'N29_', 'N30_'))]].values))
        ]
    }
    
    summary_file = output_dir / 'simulation_summary.csv'
    pd.DataFrame(summary_stats).to_csv(summary_file, index=False)
    logger.info(f"Summary statistics saved to: {summary_file}")

def main():
    """Main function to run the complete Monte Carlo analysis."""
    
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    logger.info("ROIC Monte Carlo Simulation")
    logger.debug("=" * 50)
    
    # Run simulation
    df_results = run_monte_carlo_simulation(n_simulations=10000)
    
    # Analyze results
    regression_table = analyze_results(df_results)
    
    # Save results
    save_results(df_results, regression_table)
    
    logger.info("Analysis complete")
    logger.info("Check the 'data/' directory for output files.")

if __name__ == "__main__":
    main()
