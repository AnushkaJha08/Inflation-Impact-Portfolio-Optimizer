from database import User, FinancialProfile, Portfolio, InflationData, get_db_session
import datetime
import json
import logging
import sqlalchemy.exc
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_user(username, email=None):
    """Create a new user"""
    session = get_db_session()
    
    try:
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            return existing_user
        
        user = User(username=username, email=email)
        session.add(user)
        session.commit()
        
        create_default_profile(user.id)
        create_default_portfolio(user.id)
        
        return user
    except sqlalchemy.exc.OperationalError as e:
        logger.error(f"Database error when creating user: {e}")
        st.error("Unable to connect to the database. Using local session only.")
        temp_user = User(username=username, email=email)
        temp_user.id = 1 
        return temp_user
    except Exception as e:
        logger.error(f"Unexpected error when creating user: {e}")
        st.error(f"An error occurred: {e}")
        return None
    finally:
        session.close()

def get_user_by_username(username):
    """Get a user by username"""
    session = get_db_session()
    try:
        user = session.query(User).filter(User.username == username).first()
        return user
    except sqlalchemy.exc.OperationalError as e:
        logger.error(f"Database error when getting user by username: {e}")
        st.error("Unable to connect to the database. Using local session data.")
        return None
    finally:
        session.close()

def get_user_by_id(user_id):
    """Get a user by ID"""
    session = get_db_session()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return user

def create_default_profile(user_id):
    """Create a default financial profile for a user"""
    session = get_db_session()
    
    existing_profile = session.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
    if existing_profile:
        session.close()
        return existing_profile
    
    profile = FinancialProfile(
        user_id=user_id,
        name="Default Profile",
        income=50000,
        expenses=30000,
        investments=100000,
        age=30,
        risk_tolerance="Moderate",
        investment_horizon=10
    )
    
    session.add(profile)
    session.commit()
    session.close()
    return profile

def get_user_profiles(user_id):
    """Get all financial profiles for a user"""
    session = get_db_session()
    profiles = session.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).all()
    session.close()
    return profiles

def get_profile_by_id(profile_id):
    """Get a financial profile by ID"""
    session = get_db_session()
    profile = session.query(FinancialProfile).filter(FinancialProfile.id == profile_id).first()
    session.close()
    return profile

def update_profile(profile_id, data):
    """Update a financial profile"""
    session = get_db_session()
    profile = session.query(FinancialProfile).filter(FinancialProfile.id == profile_id).first()
    
    if profile:
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        session.commit()
    
    session.close()
    return profile

def create_default_portfolio(user_id):
    """Create a default portfolio for a user"""
    session = get_db_session()
    existing_portfolio = session.query(Portfolio).filter(Portfolio.user_id == user_id).first()
    if existing_portfolio:
        session.close()
        return existing_portfolio
    
    default_allocation = {
        'Equity': 0.5,
        'Debt': 0.3,
        'Gold': 0.1,
        'Real Estate': 0.05,
        'Cash': 0.05
    }
    
    portfolio = Portfolio(
        user_id=user_id,
        name="Default Portfolio",
        allocation=default_allocation
    )
    
    session.add(portfolio)
    session.commit()
    session.close()
    return portfolio

def get_user_portfolios(user_id):
    """Get all portfolios for a user"""
    session = get_db_session()
    portfolios = session.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    session.close()
    return portfolios

def get_portfolio_by_id(portfolio_id):
    """Get a portfolio by ID"""
    session = get_db_session()
    portfolio = session.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    session.close()
    return portfolio

def update_portfolio(portfolio_id, name=None, allocation=None):
    """Update a portfolio"""
    session = get_db_session()
    portfolio = session.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    
    if portfolio:
        if name:
            portfolio.name = name
        
        if allocation:
            portfolio.set_allocation(allocation)
        
        session.commit()
    
    session.close()
    return portfolio

def get_latest_inflation_data():
    """Get the latest inflation data"""
    session = get_db_session()
    inflation_data = session.query(InflationData).order_by(InflationData.date.desc()).first()
    session.close()
    
    if inflation_data:
        return inflation_data.to_dict()
    return None

def update_inflation_data(current_rate, expected_average, category_rates, historical_data=None):
    """Update inflation data or create a new entry"""
    session = get_db_session()
    
    new_data = InflationData(
        date=datetime.datetime.now(),
        current_rate=current_rate,
        expected_average=expected_average,
        category_rates=category_rates,
        historical_data=historical_data
    )
    
    session.add(new_data)
    session.commit()
    session.close()
    return new_data.to_dict()