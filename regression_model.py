import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
import os

# Set Plotly appearance for consistent vibes
plt.style.use('bmh')

def load_data():
    """Load and clean data for regression."""
    try:
        df = pd.read_csv("base_motos_VIP_mestre.csv")
    except FileNotFoundError:
        print("Data file 'base_motos_VIP_mestre.csv' not found.")
        return None
    
    # Handle future-dated 2026 entries as 2025 (as seen in main.py)
    df.loc[df['ano_modelo'] == 2026, 'ano_modelo'] = 2025
    return df

def run_regression_by_model(df, brand, model):
    """Run linear regression for a specific brand/model."""
    # Filter data
    data = df[(df['nome_marca'].str.lower() == brand.lower()) & 
              (df['nome_modelo'].str.lower() == model.lower())].copy()
    
    if len(data) < 3:
        print(f"Error: Not enough data points (needed at least 3, found {len(data)}) for {brand} {model}.")
        return None
    
    # Pre-process
    data = data.sort_values(by='ano_modelo')
    X = data[['ano_modelo']].values  # Independent variable
    y = data['preco_limpo'].values   # Target variable
    
    # Initialize and fit Linear Regression model
    model_obj = LinearRegression()
    model_obj.fit(X, y)
    
    # Predictions and Metrics
    y_pred = model_obj.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    coef = model_obj.coef_[0]
    intercept = model_obj.intercept_
    
    print("\n" + "="*50)
    print(f"Linear Regression Results: {brand.upper()} {model.upper()}")
    print("="*50)
    print(f"Equation: Price = {coef:,.2f} * Year + ({intercept:,.2f})")
    print(f"R-squared: {r2:.4f} (Fit quality)")
    print(f"Mean Absolute Error: R$ {mae:,.2f} (Avg deviation)")
    print(f"Average Annual Variation: R$ {coef:,.2f} / year")
    
    if coef > 0:
        print("Verdict: Data shows an appreciative trend (Price increases with year).")
    else:
        print("Verdict: Data shows a degenerative trend (Depreciation).")
    
    # Visualize
    plt.figure(figsize=(12, 7))
    sns.scatterplot(x='ano_modelo', y='preco_limpo', data=data, color='blue', s=100, label='Actual Historical Prices')
    plt.plot(X, y_pred, color='red', linewidth=3, linestyle='--', 
             label=f'Linear Regression (R²={r2:.2f})\nTrend: R$ {coef:,.2f}/year')
    
    # Annotate with the equation
    plt.text(X.min(), y.max() * 0.95, f"Price = {coef:,.0f}x + {intercept:,.0f}", 
             color='red', fontsize=12, fontweight='bold', bbox=dict(facecolor='white', alpha=0.5))
    
    plt.title(f'Depreciation/Appreciation Analysis: {brand} {model}', fontsize=16)
    plt.xlabel('Model Year', fontsize=12)
    plt.ylabel('Market Price (R$)', fontsize=12)
    plt.legend(loc='lower right', fontsize=11)
    plt.grid(True, alpha=0.3)
    
    output_png = f"regression_{brand}_{model}.png".replace(" ", "_").lower()
    plt.savefig(output_png, bbox_inches='tight')
    print(f"Regression plot saved to: {output_png}")
    print("="*50 + "\n")
    
    return output_png

def main():
    df = load_data()
    if df is None: return
    
    print("MotoExpert AI - Linear Regression Analyst")
    print("-" * 50)
    
    # Get models with enough data (5+ years)
    model_counts = df.groupby(['nome_marca', 'nome_modelo']).size()
    rich_data_models = model_counts[model_counts >= 10].index.tolist()
    
    results = []
    
    print(f"\nAnalyzing {len(rich_data_models)} models with 10+ years of data...")
    
    for brand, model in rich_data_models:
        data = df[(df['nome_marca'] == brand) & (df['nome_modelo'] == model)].copy()
        X = data[['ano_modelo']].values
        y = data['preco_limpo'].values
        
        reg = LinearRegression()
        reg.fit(X, y)
        r2 = reg.score(X, y)
        coef = reg.coef_[0]
        
        results.append({
            'brand': brand,
            'model': model,
            'r2': r2,
            'variation': coef,
            'years': len(data)
        })
    
    # Sort by R-squared to find "most predictable" models
    predictable = sorted(results, key=lambda x: x['r2'], reverse=True)
    
    print("\nTop 5 Most Predictable Models (highest R²):")
    for i, res in enumerate(predictable[:5]):
        print(f"{i+1}. {res['brand']} {res['model']}: R² = {res['r2']:.4f}, Trend: R$ {res['variation']:,.2f}/year")
    
    # Run/Demo for the #1 model
    if predictable:
        run_regression_by_model(df, predictable[0]['brand'], predictable[0]['model'])

if __name__ == "__main__":
    main()
