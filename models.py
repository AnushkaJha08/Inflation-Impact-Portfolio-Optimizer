import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

def forecast_inflation(inflation_data, periods=12):
    """
    Forecasts inflation for the given number of periods.
    
    Parameters:
    - inflation_data: Dictionary containing current inflation data
    - periods: Number of future periods to forecast
    
    Returns:
    - Dictionary with forecast data
    """
    current_rate = inflation_data['current_rate']
    historical_rates = inflation_data.get('historical_rates', [])
    target_rate = inflation_data.get('target_rate', 4.0)
    
    forecasted_rates = []
    last_rate = current_rate
    
    reversion_speed = 0.2  
    volatility = 0.5       
    
    for i in range(periods):
        mean_reversion = reversion_speed * (target_rate - last_rate)
        
        shock = np.random.normal(0, volatility)
        
        next_rate = last_rate + mean_reversion + shock
        
        next_rate = max(1.0, min(12.0, next_rate))
        
        forecasted_rates.append(next_rate)
        last_rate = next_rate
    
    start_date = datetime.now()
    forecast_dates = [start_date + timedelta(days=30*i) for i in range(periods)]
    
    forecast = {
        'dates': [date.strftime('%Y-%m') for date in forecast_dates],
        'rates': forecasted_rates,
        'expected_average': sum(forecasted_rates) / len(forecasted_rates)
    }
    
    return forecast

def simulate_scenarios(inflation_data, user_data, years=5):
    """
    Simulate different inflation scenarios and their impact on purchasing power
    
    Parameters:
    - inflation_data: Dictionary containing current inflation data
    - user_data: Dictionary containing user financial data
    - years: Number of years to simulate
    
    Returns:
    - List of dictionaries containing scenario simulations
    """
    current_inflation = inflation_data['current_rate']
    
    scenarios = [
        {
            'name': 'Expected',
            'inflation_path': [current_inflation * (0.95 + 0.1 * np.random.randn()) for _ in range(years)]
        },
        {
            'name': 'High Inflation',
            'inflation_path': [current_inflation * (1.2 + 0.15 * np.random.randn()) for _ in range(years)]
        },
        {
            'name': 'Low Inflation',
            'inflation_path': [current_inflation * (0.7 + 0.1 * np.random.randn()) for _ in range(years)]
        }
    ]
    
    for scenario in scenarios:
        purchasing_power = [1.0] 
        
        for yearly_inflation in scenario['inflation_path']:
            next_pp = purchasing_power[-1] / (1 + yearly_inflation/100)
            purchasing_power.append(next_pp)
        
        scenario['purchasing_power'] = purchasing_power
    
    return scenarios

def analyze_portfolio_performance(initial_investment, portfolio_allocation, inflation_data, years=5):
    """
    Analyze portfolio performance under different scenarios
    
    Parameters:
    - initial_investment: Initial investment amount
    - portfolio_allocation: Dictionary of portfolio allocation
    - inflation_data: Dictionary containing inflation data
    - years: Number of years to analyze
    
    Returns:
    - List of dictionaries containing scenario analyses
    """
    expected_returns = {
        'Equity': 12.0,
        'Debt': 7.5,
        'Gold': 8.0,
        'Real Estate': 9.0,
        'Cash': 5.5
    }
    
    portfolio_return = sum(
        expected_returns[asset] * allocation
        for asset, allocation in portfolio_allocation.items()
    )
    
    volatility = {
        'Equity': 18.0,
        'Debt': 6.0,
        'Gold': 12.0,
        'Real Estate': 10.0,
        'Cash': 0.5
    }
    
    portfolio_volatility = sum(
        volatility[asset] * allocation
        for asset, allocation in portfolio_allocation.items()
    )
    
    scenarios = [
        {
            'name': 'Expected',
            'return_multiplier': 1.0,
            'volatility_multiplier': 1.0
        },
        {
            'name': 'Optimistic',
            'return_multiplier': 1.2,
            'volatility_multiplier': 0.8
        },
        {
            'name': 'Pessimistic',
            'return_multiplier': 0.8,
            'volatility_multiplier': 1.2
        }
    ]
    
    np.random.seed(42)  
    
    for scenario in scenarios:
        adjusted_return = portfolio_return * scenario['return_multiplier']
        adjusted_volatility = portfolio_volatility * scenario['volatility_multiplier']
        
        values = [initial_investment]
        
        for _ in range(years):
            yearly_return = np.random.lognormal(
                mean=np.log(1 + adjusted_return/100) - 0.5 * (adjusted_volatility/100)**2,
                sigma=adjusted_volatility/100
            ) - 1
            
            next_value = values[-1] * (1 + yearly_return)
            values.append(next_value)
        
        scenario['values'] = values
    
    return scenarios

def calculate_portfolio_real_performance(portfolio_allocation, inflation_rate, years=5):
    """
    Calculate the expected real (inflation-adjusted) performance of a portfolio
    
    Parameters:
    - portfolio_allocation: Dictionary of portfolio allocation
    - inflation_rate: Current inflation rate
    - years: Number of years to analyze
    
    Returns:
    - Dictionary with real performance metrics
    """
    expected_returns = {
        'Equity': 12.0,
        'Debt': 7.5,
        'Gold': 8.0,
        'Real Estate': 9.0,
        'Cash': 5.5
    }
    nominal_return = sum(
        expected_returns[asset] * allocation
        for asset, allocation in portfolio_allocation.items()
    )
    real_return = nominal_return - inflation_rate
    
    nominal_multiplier = (1 + nominal_return/100) ** years
    real_multiplier = (1 + real_return/100) ** years
    
    return {
        'nominal_return': nominal_return,
        'real_return': real_return,
        'nominal_multiplier': nominal_multiplier,
        'real_multiplier': real_multiplier,
        'years': years
    }
