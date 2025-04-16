import os
import time
import logging
from sqlalchemy import create_engine, Column, Integer, Float, String, JSON, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import sqlalchemy.exc
import datetime
import json
import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL from environment variables or use SQLite as fallback
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///app.db')

# Create engine with connection pooling and retry mechanism
def get_engine(retries=3):
    """Create a database engine with retry logic"""
    for attempt in range(retries):
        try:
            # Create engine with connection pool settings
            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,  # Test connections before using them
                pool_recycle=3600    # Recycle connections after an hour
            )
            # Verify connection works
            connection = engine.connect()
            connection.close()
            return engine
        except sqlalchemy.exc.OperationalError as e:
            logger.warning(f"Database connection attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(1)  # Wait before retrying
            else:
                st.error(f"Could not connect to database. Please try again later: {e}")
                logger.error(f"Could not establish database connection after {retries} attempts: {e}")
                # Return a memory SQLite engine as fallback
                return create_engine('sqlite:///:memory:')

# Create engine
engine = get_engine()

# Create declarative base
Base = declarative_base()

# Define models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    profiles = relationship("FinancialProfile", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class FinancialProfile(Base):
    __tablename__ = 'financial_profiles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, default="Default Profile")
    income = Column(Float, default=0.0)
    expenses = Column(Float, default=0.0)
    investments = Column(Float, default=0.0)
    age = Column(Integer)
    risk_tolerance = Column(String)  # Conservative, Moderate, Aggressive
    investment_horizon = Column(Integer)  # years
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profiles")
    
    def __repr__(self):
        return f"<FinancialProfile(id={self.id}, user_id={self.user_id}, name='{self.name}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'income': self.income,
            'expenses': self.expenses,
            'investments': self.investments,
            'age': self.age,
            'risk_tolerance': self.risk_tolerance,
            'investment_horizon': self.investment_horizon,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Portfolio(Base):
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, default="Default Portfolio")
    allocation = Column(JSON, nullable=False)  # Store as JSON: {'Equity': 0.6, 'Debt': 0.3, 'Gold': 0.1}
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, name='{self.name}')>"
    
    def get_allocation(self):
        """Get portfolio allocation as a dictionary"""
        if isinstance(self.allocation, str):
            return json.loads(self.allocation)
        return self.allocation
    
    def set_allocation(self, allocation_dict):
        """Set portfolio allocation from a dictionary"""
        if isinstance(allocation_dict, dict):
            self.allocation = allocation_dict
        else:
            raise ValueError("Allocation must be a dictionary")
            
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'allocation': self.get_allocation(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class InflationData(Base):
    __tablename__ = 'inflation_data'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    current_rate = Column(Float, nullable=False)
    expected_average = Column(Float, nullable=False)
    historical_data = Column(JSON)  # Store as JSON array of objects
    category_rates = Column(JSON)  # Store as JSON object with category keys
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<InflationData(id={self.id}, date='{self.date}', current_rate={self.current_rate})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'current_rate': self.current_rate,
            'expected_average': self.expected_average,
            'historical_data': self.historical_data,
            'category_rates': self.category_rates,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Create all tables
Base.metadata.create_all(engine)

# Session factory
SessionLocal = sessionmaker(bind=engine)

def get_db_session():
    """Get a database session"""
    try:
        db = SessionLocal()
        # Test connection with proper text() wrapper
        db.execute(text("SELECT 1"))
        return db
    except sqlalchemy.exc.OperationalError as e:
        logger.error(f"Failed to get database session: {e}")
        st.error("Database connection issue. Some features may be limited.")
        # Return a session from a memory-based SQLite database as fallback
        memory_engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(memory_engine)
        memory_session = sessionmaker(bind=memory_engine)
        return memory_session()
    except Exception as e:
        logger.error(f"Unexpected error when getting database session: {e}")
        # Return a session from a memory-based SQLite database as fallback
        memory_engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(memory_engine)
        memory_session = sessionmaker(bind=memory_engine)
        return memory_session()

def init_db():
    """Initialize database with default data if needed"""
    try:
        session = get_db_session()
        
        # Check if we have inflation data
        try:
            inflation_data = session.query(InflationData).first()
            if not inflation_data:
                # Create default inflation data (similar to what we have in inflation_data.py)
                default_inflation = InflationData(
                    date=datetime.datetime.now(),
                    current_rate=5.5,
                    expected_average=5.0,
                    historical_data=[
                        {"date": (datetime.datetime.now() - datetime.timedelta(days=30*i)).isoformat(), "rate": 5.5 - (i*0.1)}
                        for i in range(12)
                    ],
                    category_rates={
                        "Food": 7.2,
                        "Housing": 4.5,
                        "Transportation": 6.3,
                        "Healthcare": 5.8,
                        "Education": 5.7,
                        "Others": 4.5
                    }
                )
                session.add(default_inflation)
                session.commit()
                logger.info("Initialized database with default inflation data")
        except sqlalchemy.exc.OperationalError as e:
            logger.error(f"Database error during initialization: {e}")
            st.warning("Could not initialize database with default data. Some features may be limited.")
        except Exception as e:
            logger.error(f"Unexpected error during database initialization: {e}")
            st.warning(f"Database initialization error: {e}")
    finally:
        if 'session' in locals():
            session.close()