import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import streamlit as st
from db_manager import get_latest_inflation_data as get_db_inflation_data, update_inflation_data

def get_latest_inflation_data():
    """
    Get the latest inflation data for India from database or APIs
    
    First tries to get data from the database. If not available,
    it generates sample data (in a real app, this would fetch from APIs)
    and stores it in the database.
    
    Returns:
    - Dictionary with inflation data
    """
    inflation_data = get_db_inflation_data()
    
    if inflation_data:
        st.session_state.inflation_data = inflation_data
        return inflation_data

    current_date = datetime.now()
    
    historical_dates = [(current_date - timedelta(days=30*i)).strftime('%Y-%m') for i in range(12, 0, -1)]
    
    historical_rates = [
        5.7, 6.0, 6.3, 5.9, 5.5, 5.1, 4.9, 5.2, 5.6, 5.8, 5.7, 5.3
    ]
    
    current_rate = 5.1  
    category_rates = {
        'Food': 7.8,
        'Housing': 4.5,
        'Clothing': 5.2,
        'Transportation': 5.7,
        'Healthcare': 6.9,
        'Education': 5.7,
        'Communication': 3.1,
        'Recreation': 4.3,
        'Others': 4.5
    }
    
    historical_data = []
    for i in range(len(historical_dates)):
        historical_data.append({
            'date': historical_dates[i],
            'rate': historical_rates[i]
        })
    
    avg_inflation = sum(historical_rates) / len(historical_rates)
    min_inflation = min(historical_rates)
    max_inflation = max(historical_rates)
    
    expected_average = 5.5  
    target_rate = 4.0  
    
    inflation_data = {
        'current_rate': current_rate,
        'previous_rate': historical_rates[0],
        'historical_dates': historical_dates,
        'historical_rates': historical_rates,
        'avg_inflation': avg_inflation,
        'min_inflation': min_inflation,
        'max_inflation': max_inflation,
        'target_rate': target_rate,
        'expected_average': expected_average,
        'category_rates': category_rates
    }
    
    update_inflation_data(
        current_rate=current_rate, 
        expected_average=expected_average,
        category_rates=category_rates,
        historical_data=historical_data
    )
    
    st.session_state.inflation_data = inflation_data
    
    return inflation_data

def update_inflation_data_from_api():
    """
    Update inflation data from external APIs
    
    In a real application, this would fetch from actual APIs.
    For this demo, we'll simulate an API update with slight variations.
    """
    current_data = get_latest_inflation_data()
    
    current_rate = round(current_data['current_rate'] * (1 + (np.random.random() * 0.1 - 0.05)), 1)
    expected_average = round(current_data['expected_average'] * (1 + (np.random.random() * 0.05 - 0.025)), 1)
    
    category_rates = {}
    for category, rate in current_data['category_rates'].items():
        category_rates[category] = round(rate * (1 + (np.random.random() * 0.08 - 0.04)), 1)
    
    historical_data = []
    for i in range(len(current_data['historical_dates'])):
        historical_data.append({
            'date': current_data['historical_dates'][i],
            'rate': current_data['historical_rates'][i]
        })
    
    current_date = datetime.now()
    newest_month = current_date.strftime('%Y-%m')
    historical_data.append({
        'date': newest_month,
        'rate': current_rate
    })
    
    if len(historical_data) > 12:
        historical_data = historical_data[1:]
    
    update_inflation_data(
        current_rate=current_rate, 
        expected_average=expected_average,
        category_rates=category_rates,
        historical_data=historical_data
    )
    
    if 'inflation_data' in st.session_state:
        del st.session_state.inflation_data
    
    return True
