import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import base64
import os

from data_manager import (
    get_user_financial_data,
    save_user_financial_data,
    DEFAULT_PORTFOLIO_ALLOCATION
)
from report_generator import generate_report_file
from models import (
    forecast_inflation,
    simulate_scenarios,
    analyze_portfolio_performance
)
from recommendations import generate_investment_recommendations
from visualizations import (
    plot_portfolio_allocation,
    plot_inflation_forecast,
    plot_portfolio_growth,
    plot_scenario_comparison
)
from inflation_data import get_latest_inflation_data
from utils import calculate_real_returns, calculate_portfolio_value, asset_class_descriptions
from auth import require_login, login_page, logout, get_current_username

st.set_page_config(
    page_title="Inflation Impact Forecaster",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

SECTIONS = ["Dashboard", "Financial Profile", "Inflation Impact", "Portfolio Analysis", "Recommendations"]

def main():
    if not require_login():
        return  
    st.sidebar.title("Inflation Impact Forecaster")
    st.sidebar.markdown("### AI-Driven Financial Planning Tool")
    
    username = get_current_username()
    st.sidebar.markdown(f"**Logged in as:** {username}")
    if st.sidebar.button("Logout"):
        logout()
        return
    
    selected_section = st.sidebar.radio("Navigate", SECTIONS)
    
    user_data = get_user_financial_data()
    
    if 'inflation_data' not in st.session_state:
        st.session_state.inflation_data = get_latest_inflation_data()
    
    if selected_section == "Dashboard":
        show_dashboard()
    elif selected_section == "Financial Profile":
        show_financial_profile()
    elif selected_section == "Inflation Impact":
        show_inflation_impact()
    elif selected_section == "Portfolio Analysis":
        show_portfolio_analysis()
    elif selected_section == "Recommendations":
        show_recommendations()

def show_dashboard():
    st.title("Financial Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    current_inflation = st.session_state.inflation_data['current_rate']
    
    if 'previous_rate' in st.session_state.inflation_data:
        previous_rate = st.session_state.inflation_data['previous_rate']
        delta = f"{current_inflation - previous_rate:.2f}%"
    else:
        if 'historical_rates' in st.session_state.inflation_data and len(st.session_state.inflation_data['historical_rates']) > 0:
            previous_rate = st.session_state.inflation_data['historical_rates'][0]
            delta = f"{current_inflation - previous_rate:.2f}%"
        else:
            delta = "0.00%"
    
    col1.metric(
        "Current Inflation", 
        f"{current_inflation:.2f}%",
        delta
    )
    
    savings = st.session_state.user_data['savings']
    savings_impact = savings * (1 - current_inflation/100)
    col2.metric(
        "Real Savings Value (1 yr)", 
        f"₹{savings_impact:,.2f}", 
        f"-₹{savings - savings_impact:,.2f}"
    )
    
    current_portfolio = st.session_state.user_data['investments']
    col3.metric(
        "Current Portfolio", 
        f"₹{current_portfolio:,.2f}", 
        None
    )
    
    expected_return = calculate_real_returns(st.session_state.user_data['portfolio_allocation'])
    col4.metric(
        "Expected Real Return", 
        f"{expected_return - current_inflation:.2f}%", 
        f"{expected_return:.2f}% nominal"
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Portfolio Allocation")
        fig = plot_portfolio_allocation(st.session_state.user_data['portfolio_allocation'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Inflation Forecast (Next 5 Years)")
        inflation_forecast = forecast_inflation(st.session_state.inflation_data, periods=5)
        fig = plot_inflation_forecast(inflation_forecast)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("Portfolio Growth Projection (Inflation Adjusted)")
    portfolio_projection = calculate_portfolio_value(
        st.session_state.user_data['investments'],
        st.session_state.user_data['portfolio_allocation'],
        st.session_state.inflation_data,
        years=5
    )
    fig = plot_portfolio_growth(portfolio_projection)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("Recent Economic Indicators")
    
    economic_data = {
        'Indicator': ['GDP Growth', 'Repo Rate', 'Food Inflation', 'Fuel Inflation', 'Core Inflation'],
        'Value': ['7.2%', '6.50%', '8.7%', '5.3%', '4.9%'],
        'Change': ['+0.3%', '0.0%', '+1.2%', '-0.5%', '-0.1%']
    }
    
    st.dataframe(pd.DataFrame(economic_data), hide_index=True, use_container_width=True)

def show_financial_profile():
    st.title("Your Financial Profile")
    st.markdown("Let's gather some information about your financial situation to provide personalized recommendations.")
    
    with st.form("financial_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            income_value = int(st.session_state.user_data['income'])
            income = st.number_input(
                "Monthly Income (₹)",
                min_value=0,
                value=income_value,
                step=1000,
                format="%d"
            )
            
            expenses_value = int(st.session_state.user_data['expenses'])
            expenses = st.number_input(
                "Monthly Expenses (₹)",
                min_value=0,
                value=expenses_value,
                step=1000,
                format="%d"
            )
            
            savings_value = int(st.session_state.user_data['savings'])
            savings = st.number_input(
                "Current Savings (₹)",
                min_value=0,
                value=savings_value,
                step=10000,
                format="%d"
            )
            
            investments_value = int(st.session_state.user_data['investments'])
            investments = st.number_input(
                "Current Investments (₹)",
                min_value=0,
                value=investments_value,
                step=10000,
                format="%d"
            )
            
        with col2:
            risk_tolerance = st.selectbox(
                "Risk Tolerance",
                options=["Conservative", "Moderate", "Aggressive"],
                index=["Conservative", "Moderate", "Aggressive"].index(st.session_state.user_data['risk_tolerance'])
            )
            
            age = st.number_input(
                "Your Age",
                min_value=18,
                max_value=100,
                value=st.session_state.user_data.get('age', 30),
                step=1,
                format="%d"
            )
            
            investment_horizon = st.slider(
                "Investment Horizon (years)",
                min_value=1,
                max_value=30,
                value=st.session_state.user_data['investment_horizon']
            )
            
            st.markdown("### Current Portfolio Allocation")
            st.markdown("Adjust the sliders to match your current investment allocation:")
            
            portfolio = st.session_state.user_data['portfolio_allocation']
            
            equity = st.slider("Equity", 0, 100, int(portfolio.get('Equity', 0)*100))
            debt = st.slider("Debt/Bonds", 0, 100, int(portfolio.get('Debt', 0)*100))
            gold = st.slider("Gold", 0, 100, int(portfolio.get('Gold', 0)*100))
            real_estate = st.slider("Real Estate", 0, 100, int(portfolio.get('Real Estate', 0)*100))
            cash = st.slider("Cash/Bank Deposits", 0, 100, int(portfolio.get('Cash', 0)*100))
            
            total = equity + debt + gold + real_estate + cash
            if total != 100:
                st.warning(f"Allocation percentages should sum to 100% (current: {total}%)")
            
            portfolio = {
                'Equity': equity/100,
                'Debt': debt/100,
                'Gold': gold/100,
                'Real Estate': real_estate/100,
                'Cash': cash/100
            }
        
        submit_button = st.form_submit_button("Save Financial Profile")
        
        if submit_button:
            if total != 100:
                st.error("Cannot save. Allocation percentages must sum to 100%")
            else:
                st.session_state.user_data.update({
                    'income': income,
                    'expenses': expenses,
                    'savings': savings,
                    'investments': investments,
                    'portfolio_allocation': portfolio,
                    'risk_tolerance': risk_tolerance,
                    'investment_horizon': investment_horizon,
                    'age': age
                })
                
                save_user_financial_data(st.session_state.user_data)
                
                st.success("Financial profile saved successfully!")
                st.balloons()

    st.markdown("---")
    st.subheader("Asset Class Information")
    
    for asset, description in asset_class_descriptions.items():
        with st.expander(f"About {asset}"):
            st.write(description)

def show_inflation_impact():
    st.title("Inflation Impact Analysis")
    
    st.subheader("Your Current Financial Overview")
    
    col1, col2, col3 = st.columns(3)
    
    monthly_income = st.session_state.user_data['income']
    monthly_expenses = st.session_state.user_data['expenses']
    monthly_savings = monthly_income - monthly_expenses
    
    col1.metric("Monthly Income", f"₹{monthly_income:,}")
    col2.metric("Monthly Expenses", f"₹{monthly_expenses:,}")
    col3.metric("Monthly Savings", f"₹{monthly_savings:,}")
    
    st.markdown("---")
    
    st.subheader("Inflation Impact Simulation")
    
    years = st.slider("Projection Years", 1, 20, 5)
    
    scenarios = simulate_scenarios(
        st.session_state.inflation_data,
        st.session_state.user_data,
        years
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Purchasing Power Impact")
        fig = go.Figure()
        
        for scenario in scenarios:
            fig.add_trace(go.Scatter(
                x=list(range(years+1)),
                y=scenario['purchasing_power'],
                mode='lines',
                name=f"{scenario['name']} Scenario"
            ))
        
        fig.update_layout(
            xaxis_title="Years",
            yaxis_title="Purchasing Power (₹1 Value)",
            legend_title="Scenarios",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        **Understanding Purchasing Power Impact:**
        
        This chart shows how ₹1 today will be worth less in the future due to inflation.
        For example, if the line drops to ₹0.70 in year 5, it means that what costs ₹1 today
        will cost approximately ₹1.43 in 5 years (since 1/0.70 ≈ 1.43).
        """)
    
    with col2:
        st.markdown("### Savings Erosion")
        
        current_savings = st.session_state.user_data['savings']
        
        fig = go.Figure()
        
        for scenario in scenarios:
            savings_value = [current_savings * pp for pp in scenario['purchasing_power']]
            
            fig.add_trace(go.Scatter(
                x=list(range(years+1)),
                y=savings_value,
                mode='lines',
                name=f"{scenario['name']} Scenario"
            ))
        
        fig.update_layout(
            xaxis_title="Years",
            yaxis_title="Real Value of Current Savings (₹)",
            legend_title="Scenarios",
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        **Understanding Savings Erosion:**
        
        This chart shows how the real value (purchasing power) of your current savings
        will decrease over time if kept in cash due to inflation. This highlights
        the importance of investing your savings to at least beat inflation.
        """)
    
    st.markdown("---")
    
    st.subheader("Inflation Impact on Monthly Expenses")
    
    expense_categories = {
        "Housing": 0.30,
        "Food": 0.25,
        "Transportation": 0.15,
        "Healthcare": 0.10,
        "Education": 0.10,
        "Others": 0.10
    }
    
    category_inflation_rates = {
        "Housing": st.session_state.inflation_data['category_rates'].get('Housing', 4.5),
        "Food": st.session_state.inflation_data['category_rates'].get('Food', 7.8),
        "Transportation": st.session_state.inflation_data['category_rates'].get('Transportation', 5.2),
        "Healthcare": st.session_state.inflation_data['category_rates'].get('Healthcare', 6.9),
        "Education": st.session_state.inflation_data['category_rates'].get('Education', 5.7),
        "Others": st.session_state.inflation_data['category_rates'].get('Others', 4.5)
    }
    
    current_expenses = {
        category: st.session_state.user_data['expenses'] * ratio 
        for category, ratio in expense_categories.items()
    }
    
    projection_year = st.select_slider("Select Year for Projection", options=list(range(1, years+1)))
    
    future_expenses = {
        category: amount * ((1 + rate/100) ** projection_year)
        for category, amount in current_expenses.items()
        for rate in [category_inflation_rates[category]]
    }
    
    total_current = sum(current_expenses.values())
    total_future = sum(future_expenses.values())
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### Current Monthly Expenses (₹{total_current:,.2f})")
        
        fig = px.pie(
            values=list(current_expenses.values()),
            names=list(current_expenses.keys()),
            title="Current Expense Breakdown"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        expense_df = pd.DataFrame({
            'Category': current_expenses.keys(),
            'Amount (₹)': [f"{amount:,.2f}" for amount in current_expenses.values()],
            'Percentage': [f"{(amount/total_current)*100:.1f}%" if total_current > 0 else "0.0%" for amount in current_expenses.values()]
        })
        st.dataframe(expense_df, hide_index=True, use_container_width=True)
    
    with col2:
        st.markdown(f"### Projected Expenses in {projection_year} Years (₹{total_future:,.2f})")
        
        fig = px.pie(
            values=list(future_expenses.values()),
            names=list(future_expenses.keys()),
            title=f"Projected Expense Breakdown (Year {projection_year})"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        future_expense_df = pd.DataFrame({
            'Category': future_expenses.keys(),
            'Amount (₹)': [f"{amount:,.2f}" for amount in future_expenses.values()],
            'Percentage': [f"{(amount/total_future)*100:.1f}%" if total_future > 0 else "0.0%" for amount in future_expenses.values()],
            'Inflation Rate': [f"{category_inflation_rates[cat]:.1f}%" for cat in future_expenses.keys()]
        })
        st.dataframe(future_expense_df, hide_index=True, use_container_width=True)
    
    st.markdown(f"### Total Expense Increase")
    if total_current > 0:
        st.info(f"Your monthly expenses are projected to increase from ₹{total_current:,.2f} to ₹{total_future:,.2f} in {projection_year} years. This represents a {((total_future/total_current)-1)*100:.1f}% increase.")
    else:
        st.info(f"Please enter your expense details in the Financial Profile section to see projected expense increases.")

def show_portfolio_analysis():
    st.title("Portfolio Analysis")
    
    if st.session_state.user_data['investments'] <= 0:
        st.warning("Please add your investment details in the Financial Profile section first.")
        return
    st.subheader("Current Portfolio Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Investments", f"₹{st.session_state.user_data['investments']:,}")
        
        fig = plot_portfolio_allocation(st.session_state.user_data['portfolio_allocation'])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Expected Returns by Asset Class")
        
        expected_returns = {
            'Equity': 12.0,
            'Debt': 7.5,
            'Gold': 8.0,
            'Real Estate': 9.0,
            'Cash': 5.5
        }
        
        current_inflation = st.session_state.inflation_data['current_rate']
        
        returns_df = pd.DataFrame({
            'Asset Class': expected_returns.keys(),
            'Expected Return (%)': [f"{ret:.1f}%" for ret in expected_returns.values()],
            'Real Return (%)': [f"{ret - current_inflation:.1f}%" for ret in expected_returns.values()],
            'Current Allocation (%)': [f"{alloc*100:.1f}%" for alloc in st.session_state.user_data['portfolio_allocation'].values()]
        })
        
        st.dataframe(returns_df, hide_index=True, use_container_width=True)
        
        weighted_return = sum(
            expected_returns[asset] * allocation
            for asset, allocation in st.session_state.user_data['portfolio_allocation'].items()
        )
        
        weighted_real_return = weighted_return - current_inflation
        
        st.metric(
            "Portfolio Expected Return", 
            f"{weighted_return:.2f}%",
            f"{weighted_real_return:.2f}% real return (after inflation)"
        )
    
    st.markdown("---")
    
    st.subheader("Portfolio Performance Simulation")
    
    years = st.slider("Simulation Horizon (Years)", 1, 30, st.session_state.user_data['investment_horizon'])
    
    portfolio_scenarios = analyze_portfolio_performance(
        st.session_state.user_data['investments'],
        st.session_state.user_data['portfolio_allocation'],
        st.session_state.inflation_data,
        years
    )
    
    fig = plot_scenario_comparison(portfolio_scenarios, years)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Scenario Details")
    
    for i, scenario in enumerate(portfolio_scenarios):
        col1, col2, col3 = st.columns(3)
        
        final_value = scenario['values'][-1]
        initial_value = scenario['values'][0]
        cagr = ((final_value / initial_value) ** (1/years) - 1) * 100
        
        col1.metric(
            f"{scenario['name']} Scenario", 
            f"₹{final_value:,.2f}",
            f"{((final_value/initial_value)-1)*100:.1f}% total growth"
        )
        
        col2.metric(
            "CAGR", 
            f"{cagr:.2f}%",
            f"{cagr - st.session_state.inflation_data['expected_average']:.2f}% real CAGR"
        )
        
        col3.metric(
            "Multiple", 
            f"{final_value/initial_value:.2f}x",
            f"in {years} years"
        )
    
    st.markdown("---")
    
    st.subheader("Risk Analysis")
    
    volatility = {
        'Equity': 18.0,
        'Debt': 6.0,
        'Gold': 12.0,
        'Real Estate': 10.0,
        'Cash': 0.5
    }
    portfolio_volatility = sum(
        volatility[asset] * allocation
        for asset, allocation in st.session_state.user_data['portfolio_allocation'].items()
    )
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Portfolio Volatility")
        st.metric("Annual Volatility", f"{portfolio_volatility:.2f}%")
        
        risk_level = "Low"
        if portfolio_volatility > 15:
            risk_level = "High"
        elif portfolio_volatility > 8:
            risk_level = "Medium"
        
        st.info(f"Risk Level: {risk_level}")
        
        user_risk = st.session_state.user_data['risk_tolerance']
        
        if (risk_level == "High" and user_risk == "Conservative") or \
           (risk_level == "Low" and user_risk == "Aggressive"):
            st.warning("Your current portfolio risk level does not match your stated risk tolerance.")
        else:
            st.success("Your portfolio risk level is aligned with your stated risk tolerance.")
    
    with col2:
        st.markdown("### Risk-Return Trade-off")
        
        assets = list(volatility.keys())
        returns = [expected_returns[asset] for asset in assets]
        vols = [volatility[asset] for asset in assets]
        
        assets.append("Your Portfolio")
        returns.append(weighted_return)
        vols.append(portfolio_volatility)
        
        sizes = [50] * (len(assets)-1) + [100]
        
        colors = ["blue"] * (len(assets)-1) + ["red"]
        
        fig = px.scatter(
            x=vols,
            y=returns,
            text=assets,
            size=sizes,
            color=colors,
            labels={'x': 'Risk (Volatility %)', 'y': 'Expected Return (%)'},
            title="Risk vs. Return Analysis"
        )
        
        x_ef = np.linspace(0, 20, 100)
        y_ef = 5 + 0.3 * x_ef + 0.01 * x_ef**2  
        
        fig.add_trace(
            go.Scatter(
                x=x_ef,
                y=y_ef,
                mode='lines',
                line=dict(color='gray', dash='dash'),
                name='Efficient Frontier'
            )
        )
        
        fig.update_traces(
            marker=dict(size=sizes),
            selector=dict(mode='markers')
        )
        
        fig.update_layout(
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        **Understanding the Risk-Return Chart:**
        
        This chart shows the relationship between risk (volatility) and expected return for different asset classes.
        - The **efficient frontier** (dotted line) represents theoretically optimal portfolios.
        - Your portfolio (red dot) shows where you currently stand.
        - Aim to be as close to the efficient frontier as possible for the best risk-adjusted returns.
        """)

def show_recommendations():
    st.title("Personalized Recommendations")
    
    if st.session_state.user_data['income'] <= 0:
        st.warning("Please complete your financial profile first to get personalized recommendations.")
        return
    
    recommendations = generate_investment_recommendations(
        st.session_state.user_data,
        st.session_state.inflation_data
    )
    st.subheader("Your Current Financial Situation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Monthly Income", 
            f"₹{st.session_state.user_data['income']:,}"
        )
    
    with col2:
        st.metric(
            "Monthly Expenses", 
            f"₹{st.session_state.user_data['expenses']:,}"
        )
    
    with col3:
        if st.session_state.user_data['income'] > 0:
            savings_rate = (st.session_state.user_data['income'] - st.session_state.user_data['expenses']) / st.session_state.user_data['income'] * 100
            st.metric(
                "Savings Rate", 
                f"{savings_rate:.1f}%",
                f"₹{st.session_state.user_data['income'] - st.session_state.user_data['expenses']:,} monthly"
            )
        else:
            st.metric(
                "Savings Rate", 
                "0.0%",
                "₹0 monthly"
            )
    
    st.markdown("---")
    
    st.subheader("Recommended Portfolio Allocation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Current Allocation")
        current_fig = plot_portfolio_allocation(st.session_state.user_data['portfolio_allocation'])
        st.plotly_chart(current_fig, use_container_width=True)
    
    with col2:
        st.markdown("### Recommended Allocation")
        recommended_fig = plot_portfolio_allocation(recommendations['recommended_allocation'])
        st.plotly_chart(recommended_fig, use_container_width=True)
    
    st.markdown("### Detailed Allocation Comparison")
    
    comparison_df = pd.DataFrame({
        'Asset Class': recommendations['recommended_allocation'].keys(),
        'Current Allocation': [f"{st.session_state.user_data['portfolio_allocation'].get(asset, 0)*100:.1f}%" for asset in recommendations['recommended_allocation'].keys()],
        'Recommended Allocation': [f"{alloc*100:.1f}%" for alloc in recommendations['recommended_allocation'].values()],
        'Change': [f"{(recommendations['recommended_allocation'][asset] - st.session_state.user_data['portfolio_allocation'].get(asset, 0))*100:+.1f}%" for asset in recommendations['recommended_allocation'].keys()]
    })
    
    st.dataframe(comparison_df, hide_index=True, use_container_width=True)
    
    st.markdown("### Expected Improvement")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Current Expected Return", 
            f"{recommendations['current_return']:.2f}%"
        )
    
    with col2:
        st.metric(
            "Recommended Expected Return", 
            f"{recommendations['recommended_return']:.2f}%",
            f"{recommendations['recommended_return'] - recommendations['current_return']:+.2f}%"
        )
    
    with col3:
        st.metric(
            "Expected Inflation", 
            f"{st.session_state.inflation_data['expected_average']:.2f}%",
            f"{recommendations['recommended_return'] - st.session_state.inflation_data['expected_average']:+.2f}% real return"
        )
    
    st.markdown("---")
    
    st.subheader("Specific Investment Recommendations")
    
    for i, rec in enumerate(recommendations['specific_recommendations']):
        with st.expander(f"{i+1}. {rec['title']}"):
            st.markdown(rec['description'])
            
            if 'allocation' in rec:
                st.markdown("**Suggested Allocation:**")
                for asset, value in rec['allocation'].items():
                    st.markdown(f"- {asset}: {value}")
            
            if 'expected_return' in rec:
                st.markdown(f"**Expected Return:** {rec['expected_return']}")
            
            if 'risk_level' in rec:
                st.markdown(f"**Risk Level:** {rec['risk_level']}")
            
            if 'time_horizon' in rec:
                st.markdown(f"**Recommended Time Horizon:** {rec['time_horizon']}")
    
    
    st.subheader("General Financial Advice")
    
    advice_categories = [
        {
            "title": "Inflation Protection Strategies",
            "tips": [
                "Consider inflation-indexed bonds (IIBs) offered by the Government of India",
                "Invest in equity mutual funds for long-term inflation-beating returns",
                "Gold can serve as a hedge against high inflation periods",
                "Real estate investments in growing areas can appreciate ahead of inflation"
            ]
        },
        {
            "title": "Tax Efficiency Recommendations",
            "tips": [
                "Maximize investments in tax-saving instruments under Section 80C (up to ₹1.5 lakhs)",
                "Consider ELSS funds for tax benefits with equity-linked returns",
                "NPS contributions offer additional tax benefits under Section 80CCD(1B)",
                "Health insurance premiums are tax-deductible under Section 80D"
            ]
        },
        {
            "title": "Emergency Fund Guidelines",
            "tips": [
                f"Maintain at least ₹{st.session_state.user_data['expenses']*6:,.2f} (6 months of expenses) in liquid assets",
                "Split emergency funds between savings accounts and liquid funds for better returns",
                "Review and adjust your emergency fund size as your expenses change",
                "Consider a laddered FD approach for better liquidity and returns"
            ]
        }
    ]
    
    for category in advice_categories:
        with st.expander(category["title"]):
            for tip in category["tips"]:
                st.markdown(f"- {tip}")
    
    st.markdown("---")
    
    st.success("**Next Steps:** Review the recommended portfolio allocation and specific investment suggestions. Consider implementing these changes gradually to improve your financial resilience against inflation.")
    
    if st.button("Generate Detailed PDF Report"):
        with st.spinner("Generating PDF report..."):
            try:
                pdf_recommendations = {
                    'summary': "Based on your financial profile and current inflation trends, we recommend the following asset allocation and investment strategies to optimize your portfolio for growth while protecting against inflation.",
                    'recommended_allocation': recommendations['recommended_allocation'],
                    'specific_suggestions': {
                        'Inflation Protection': [
                            "Consider adding index-linked bonds to your portfolio",
                            "Increase allocation to equity funds with inflation-beating potential",
                            f"Maintain at least {recommendations['recommended_allocation'].get('Gold', 0)*100:.1f}% allocation to gold"
                        ],
                        'Tax Efficiency': [
                            "Maximize tax-saving investments under Section 80C",
                            "Consider ELSS funds for equity exposure with tax benefits",
                            "Utilize NPS for additional tax benefits under Section 80CCD(1B)"
                        ],
                        'Risk Management': [
                            f"Maintain emergency fund of at least ₹{st.session_state.user_data['expenses']*6:,.2f}",
                            "Consider health and term insurance for risk protection",
                            "Diversify across asset classes to reduce portfolio volatility"
                        ]
                    },
                    'action_steps': [
                        f"Rebalance your portfolio to match the recommended allocation",
                        f"Set up a Systematic Investment Plan (SIP) of ₹{int((st.session_state.user_data['income'] - st.session_state.user_data['expenses'])*0.5):,} per month",
                        f"Review and adjust your portfolio every 6 months",
                        f"Consult with a tax professional to optimize tax efficiency"
                    ]
                }
                
                pdf_path, pdf_filename = generate_report_file(
                    st.session_state.user_data,
                    st.session_state.inflation_data,
                    pdf_recommendations
                )

                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                b64_pdf = base64.b64encode(pdf_bytes).decode()
                href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_filename}">Download PDF Report</a>'
                st.markdown(href, unsafe_allow_html=True)

                try:
                    os.remove(pdf_path)
                except:
                    pass
                
                st.success("Your personalized investment report has been generated successfully!")
            except Exception as e:
                st.error(f"Error generating PDF report: {e}")
                st.info("Please try again later or contact support if the problem persists.")

if __name__ == "__main__":
    main()
