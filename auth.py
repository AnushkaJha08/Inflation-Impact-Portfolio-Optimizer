import streamlit as st
import hashlib
import logging
import sqlalchemy.exc
from db_manager import create_user, get_user_by_username

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_password(password):
    """Create hashed password"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    """Display login page"""
    st.title("User Login")
    
    with st.sidebar:
        st.subheader("Login or Register")

        with st.expander("Login", expanded=True):
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login"):
                if login_username and login_password:
                    try:
                        user = get_user_by_username(login_username)
                        
                        if user:

                            st.session_state.username = login_username
                            st.session_state.authenticated = True
                            st.success(f"Welcome back, {login_username}!")

                            st.rerun()
                        else:
                            st.error("User not found. Please register first.")
                    except sqlalchemy.exc.OperationalError as e:
                        logger.error(f"Database error during login: {e}")
                        st.error("Database connection error. Using local session.")

                        st.session_state.username = login_username
                        st.session_state.authenticated = True
                        st.warning("Connected in offline mode due to database issue.")
                        st.rerun()
                    except Exception as e:
                        logger.error(f"Unexpected error during login: {e}")
                        st.error(f"Login error: {e}")
                else:
                    st.warning("Please enter both username and password.")
        
        with st.expander("Register", expanded=False):
            register_username = st.text_input("Choose Username", key="register_username")
            register_email = st.text_input("Email (optional)", key="register_email")
            register_password = st.text_input("Choose Password", type="password", key="register_password")
            register_password_confirm = st.text_input("Confirm Password", type="password", key="register_password_confirm")
            
            if st.button("Register"):
                if register_username and register_password:
                    if register_password != register_password_confirm:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            existing_user = get_user_by_username(register_username)
                            
                            if existing_user:
                                st.error("Username already exists. Please choose another.")
                            else:
                                new_user = create_user(register_username, register_email)
                                
                                if new_user:
                                    st.session_state.username = register_username
                                    st.session_state.authenticated = True
                                    st.success(f"Welcome, {register_username}! Account created successfully.")

                                    st.rerun()
                                else:
                                    st.error("Error creating account. Please try again.")
                        except sqlalchemy.exc.OperationalError as e:
                            logger.error(f"Database error during registration: {e}")
                            st.error("Database connection error. Using local session.")

                            st.session_state.username = register_username
                            st.session_state.authenticated = True
                            st.warning("Connected in offline mode due to database issue.")
                            st.rerun()
                        except Exception as e:
                            logger.error(f"Unexpected error during registration: {e}")
                            st.error(f"Registration error: {e}")
                else:
                    st.warning("Username and password are required.")
    
    st.markdown("""
    ## AI-Driven Inflation Impact Forecaster

    Welcome to the AI-Driven Inflation Impact Forecaster for the Indian market. This tool helps you:
    
    * Visualize current inflation trends in India
    * Analyze how inflation affects your personal finances
    * Get personalized investment recommendations
    * Simulate different financial scenarios
    
    Please login or register to get started.
    """)
    
    st.image("assets/dashboard_icon.svg", width=150)

def logout():
    """Log out the current user"""
    if 'username' in st.session_state:
        del st.session_state.username
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    if 'user_data' in st.session_state:
        del st.session_state.user_data
    st.success("Logged out successfully!")
    st.rerun()

def is_authenticated():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def get_current_username():
    """Get current username"""
    return st.session_state.get('username', None)

def require_login():
    """Require login to access the page"""
    if not is_authenticated():
        login_page()
        return False
    return True