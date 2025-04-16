import json
import os
import pandas as pd
from datetime import datetime
import streamlit as st
from database import init_db
from db_manager import (
    create_user, 
    create_default_profile, 
    create_default_portfolio,
    get_user_by_username,
    get_user_profiles,
    get_user_portfolios,
    update_profile,
    update_portfolio,
    get_latest_inflation_data,
    update_inflation_data
)

init_db()

DEFAULT_PORTFOLIO_ALLOCATION = {
    'Equity': 0.30,
    'Debt': 0.30,
    'Gold': 0.15,
    'Real Estate': 0.15,
    'Cash': 0.10
}

def get_user_financial_data():
    """
    Load user financial data from database or initialize with defaults
    """
    if 'username' not in st.session_state:
        st.session_state.username = "default_user"
        
    user = get_user_by_username(st.session_state.username)
    if not user:
        user = create_user(st.session_state.username)
    
    profiles = get_user_profiles(user.id)
    portfolios = get_user_portfolios(user.id)
    profile = profiles[0] if profiles else create_default_profile(user.id)
    portfolio = portfolios[0] if portfolios else create_default_portfolio(user.id)
    
    portfolio_allocation = portfolio.get_allocation() if hasattr(portfolio, 'get_allocation') else DEFAULT_PORTFOLIO_ALLOCATION.copy()
    
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {
            'id': profile.id,
            'portfolio_id': portfolio.id,
            'income': profile.income,
            'expenses': profile.expenses,
            'savings': profile.income - profile.expenses if profile.income > 0 else 0,
            'investments': profile.investments,
            'portfolio_allocation': portfolio_allocation,
            'risk_tolerance': profile.risk_tolerance,
            'investment_horizon': profile.investment_horizon,
            'age': profile.age
        }
    
    return st.session_state.user_data

def save_user_financial_data(user_data):
    """
    Save user financial data to database and update session state
    """
    st.session_state.user_data = user_data
    
    profile_data = {
        'income': user_data.get('income', 0),
        'expenses': user_data.get('expenses', 0),
        'investments': user_data.get('investments', 0),
        'risk_tolerance': user_data.get('risk_tolerance', 'Moderate'),
        'investment_horizon': user_data.get('investment_horizon', 5),
        'age': user_data.get('age', 30)
    }
    
    update_profile(user_data.get('id'), profile_data)
    
    update_portfolio(
        user_data.get('portfolio_id'), 
        allocation=user_data.get('portfolio_allocation')
    )
    
    return True

def get_recommended_allocation(risk_profile, investment_horizon, inflation_rate):
    """
    Get recommended portfolio allocation based on risk profile and investment horizon
    
    Parameters:
    - risk_profile: 'Conservative', 'Moderate', or 'Aggressive'
    - investment_horizon: Number of years
    - inflation_rate: Current inflation rate
    
    Returns:
    - Dictionary with recommended asset allocation
    """
    allocations = {
        'Conservative': {
            'Equity': 0.20,
            'Debt': 0.40,
            'Gold': 0.15,
            'Real Estate': 0.15,
            'Cash': 0.10
        },
        'Moderate': {
            'Equity': 0.40,
            'Debt': 0.30,
            'Gold': 0.10,
            'Real Estate': 0.15,
            'Cash': 0.05
        },
        'Aggressive': {
            'Equity': 0.60,
            'Debt': 0.20,
            'Gold': 0.05,
            'Real Estate': 0.10,
            'Cash': 0.05
        }
    }
    
    allocation = allocations.get(risk_profile, allocations['Moderate']).copy()
    
    if investment_horizon > 10:
        allocation['Equity'] = min(allocation['Equity'] + 0.10, 0.70)
        allocation['Debt'] = max(allocation['Debt'] - 0.05, 0.10)
        allocation['Cash'] = max(allocation['Cash'] - 0.05, 0.05)
    elif investment_horizon < 3:
        allocation['Equity'] = max(allocation['Equity'] - 0.10, 0.10)
        allocation['Debt'] = min(allocation['Debt'] + 0.05, 0.50)
        allocation['Cash'] = min(allocation['Cash'] + 0.05, 0.20)
    
    if inflation_rate > 6.0:
        allocation['Equity'] = min(allocation['Equity'] + 0.05, 0.70)
        allocation['Gold'] = min(allocation['Gold'] + 0.05, 0.20)
        allocation['Cash'] = max(allocation['Cash'] - 0.05, 0.05)
        allocation['Debt'] = max(allocation['Debt'] - 0.05, 0.10)
    elif inflation_rate < 4.0:
        allocation['Debt'] = min(allocation['Debt'] + 0.05, 0.50)
        allocation['Cash'] = min(allocation['Cash'] + 0.05, 0.20)
        allocation['Equity'] = max(allocation['Equity'] - 0.05, 0.10)
        allocation['Gold'] = max(allocation['Gold'] - 0.05, 0.05)
    
    total = sum(allocation.values())
    normalized = {k: v/total for k, v in allocation.items()}
    
    return normalized
