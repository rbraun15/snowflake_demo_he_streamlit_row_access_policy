"""
Higher Education Finance Dashboard - Row Access Policy Demo

This Streamlit application demonstrates row access policies by showing 
financial data that is filtered based on the current user's entitlements.

- ADMIN user: Can see all departments
- MARKETING_DIRECTOR user: Can only see Marketing department data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, date
import warnings
warnings.filterwarnings('ignore')
import io
import base64
from datetime import datetime
import plotly.io as pio

# Configure Streamlit page
st.set_page_config(
    page_title="Higher Education Finance Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric > div > div > div > div {
        font-size: 1rem;
    }
    .plot-container {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .department-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def get_current_user():
    """Get the current Snowflake user from the session context"""
    try:
        current_user_query = "SELECT CURRENT_USER() as username"
        result = st.connection("snowflake").query(current_user_query)
        return result.iloc[0]['USERNAME']
    except Exception as e:
        st.error(f"Error getting current user: {str(e)}")
        return "UNKNOWN"

@st.cache_data
def load_finance_data():
    """Load finance data from the secure view (filtered by row access policy)"""
    try:
        query = """
        SELECT 
            DEPARTMENT_NAME,
            DEPARTMENT_CODE,
            TRANSACTION_DATE,
            EXPENDITURE_CATEGORY,
            AMOUNT,
            FISCAL_YEAR,
            FISCAL_MONTH,
            DIRECTOR_NAME,
            DIRECTOR_START_DATE,
            IS_CURRENT_DIRECTOR
        FROM VW_FINANCE_DATA
        ORDER BY TRANSACTION_DATE DESC, DEPARTMENT_NAME
        """
        return st.connection("snowflake").query(query)
    except Exception as e:
        st.error(f"Error loading finance data: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def load_finance_summary():
    """Load aggregated finance summary data"""
    try:
        query = """
        SELECT 
            DEPARTMENT_NAME,
            DEPARTMENT_CODE,
            FISCAL_YEAR,
            FISCAL_MONTH,
            EXPENDITURE_CATEGORY,
            TOTAL_AMOUNT,
            TRANSACTION_COUNT,
            AVERAGE_AMOUNT,
            DIRECTOR_NAME,
            DIRECTOR_START_DATE
        FROM VW_FINANCE_SUMMARY
        ORDER BY FISCAL_YEAR DESC, FISCAL_MONTH DESC, DEPARTMENT_NAME
        """
        return st.connection("snowflake").query(query)
    except Exception as e:
        st.error(f"Error loading finance summary: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def get_user_access_info(username):
    """Get user access information for display"""
    try:
        query = f"""
        SELECT 
            ue.ACCESS_LEVEL,
            d.DEPARTMENT_NAME,
            d.DEPARTMENT_CODE
        FROM USER_ENTITLEMENTS ue
        LEFT JOIN DEPARTMENTS d ON ue.DEPARTMENT_ID = d.DEPARTMENT_ID
        WHERE ue.USERNAME = '{username}' AND ue.IS_ACTIVE = TRUE
        ORDER BY d.DEPARTMENT_NAME
        """
        return st.connection("snowflake").query(query)
    except Exception as e:
        st.error(f"Error loading user access info: {str(e)}")
        return pd.DataFrame()

def format_currency(amount):
    """Format number as currency"""
    return f"${amount:,.2f}"

def create_trend_chart(df, category_filter=None):
    """Create a trend chart showing spending over time"""
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)
    
    # Filter by categories if specified
    if category_filter and len(category_filter) > 0:
        df = df[df['EXPENDITURE_CATEGORY'].isin(category_filter)]
    
    # Group by year and month
    trend_data = df.groupby(['FISCAL_YEAR', 'FISCAL_MONTH'])['AMOUNT'].sum().reset_index()
    
    # Create date using string formatting
    trend_data['DATE'] = pd.to_datetime(
        trend_data['FISCAL_YEAR'].astype(str) + '-' + 
        trend_data['FISCAL_MONTH'].astype(str).str.zfill(2) + '-01'
    )
    
    # Create title based on category filter
    title_suffix = ""
    if category_filter and len(category_filter) > 0:
        if len(category_filter) == 1:
            title_suffix = f" - {category_filter[0]}"
        elif len(category_filter) <= 3:
            title_suffix = f" - {', '.join(category_filter)}"
        else:
            title_suffix = f" - {len(category_filter)} Categories"
    
    fig = px.line(
        trend_data, 
        x='DATE', 
        y='AMOUNT',
        title=f"Spending Trend Over Time{title_suffix}",
        labels={'AMOUNT': 'Amount ($)', 'DATE': 'Date'},
        color_discrete_sequence=['#1f77b4']
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Amount ($)",
        hovermode='x unified',
        template="plotly_white",
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    fig.update_traces(
        line=dict(width=3, color='#1f77b4'),
        marker=dict(color='#1f77b4')
    )
    
    return fig

def create_category_breakdown(df, year_filter=None):
    """Create a pie chart showing expenditure category breakdown"""
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)
    
    # Filter by years if specified
    if year_filter and len(year_filter) > 0:
        df = df[df['FISCAL_YEAR'].isin(year_filter)]
    
    category_totals = df.groupby('EXPENDITURE_CATEGORY')['AMOUNT'].sum().reset_index()
    
    # Create title based on year filter
    title_suffix = ""
    if year_filter and len(year_filter) > 0:
        if len(year_filter) == 1:
            title_suffix = f" - {year_filter[0]}"
        else:
            title_suffix = f" - {min(year_filter)}-{max(year_filter)}"
    
    # Define explicit color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
    
    fig = px.pie(
        category_totals,
        values='AMOUNT',
        names='EXPENDITURE_CATEGORY',
        title=f"Expenditure Category Breakdown{title_suffix}",
        color_discrete_sequence=colors
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        textfont_color='white',
        marker=dict(line=dict(color='white', width=2))
    )
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

def create_department_comparison(df):
    """Create a bar chart comparing departments"""
    if df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)
    
    dept_totals = df.groupby(['DEPARTMENT_NAME', 'FISCAL_YEAR'])['AMOUNT'].sum().reset_index()
    
    # Define explicit color palette for departments
    dept_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    fig = px.bar(
        dept_totals,
        x='FISCAL_YEAR',
        y='AMOUNT',
        color='DEPARTMENT_NAME',
        title="Annual Spending by Department",
        labels={'AMOUNT': 'Amount ($)', 'FISCAL_YEAR': 'Fiscal Year'},
        barmode='group',
        color_discrete_sequence=dept_colors
    )
    
    fig.update_layout(
        xaxis_title="Fiscal Year",
        yaxis_title="Amount ($)",
        template="plotly_white",
        legend_title="Department",
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

def generate_complete_dashboard_html(current_user, filtered_data, finance_data, selected_department, selected_years, selected_categories, analysis_category):
    """Generate complete HTML dashboard report with charts and all content"""
    
    # Calculate summary statistics
    total_spending = filtered_data['AMOUNT'].sum()
    avg_monthly = filtered_data.groupby(['FISCAL_YEAR', 'FISCAL_MONTH'])['AMOUNT'].sum().mean()
    transaction_count = len(filtered_data)
    unique_categories = filtered_data['EXPENDITURE_CATEGORY'].nunique()
    
    # Context information
    dept_context = selected_department if selected_department != "All" else "All Departments"
    years_context = ', '.join(map(str, sorted(selected_years))) if selected_years else "No years"
    categories_context = ', '.join(selected_categories) if selected_categories and len(selected_categories) <= 5 else f"{len(selected_categories)} categories" if selected_categories else "No categories"
    
    # Generate charts as HTML
    try:
        # 1. Trend Chart
        trend_chart = create_trend_chart(filtered_data, selected_categories)
        trend_chart.update_layout(template="plotly_white", plot_bgcolor='white', paper_bgcolor='white')
        trend_chart_html = trend_chart.to_html(include_plotlyjs='inline', div_id="trend_chart", config={'displayModeBar': False})
        
        # 2. Category Breakdown
        category_chart = create_category_breakdown(filtered_data, selected_years)
        category_chart.update_layout(template="plotly_white", plot_bgcolor='white', paper_bgcolor='white')
        category_chart_html = category_chart.to_html(include_plotlyjs=False, div_id="category_chart", config={'displayModeBar': False})
        
        # 3. Department Comparison (if applicable)
        departments = sorted(filtered_data['DEPARTMENT_NAME'].unique())
        dept_chart_html = ""
        if len(departments) > 1:
            dept_chart = create_department_comparison(filtered_data)
            dept_chart.update_layout(template="plotly_white", plot_bgcolor='white', paper_bgcolor='white')
            dept_chart_html = f"""
            <div class="chart-section">
                <h3>📊 Department Comparison</h3>
                {dept_chart.to_html(include_plotlyjs=False, div_id="dept_chart", config={'displayModeBar': False})}
            </div>
            """
        
        # 4. Category Deep Dive Charts
        category_data = filtered_data[filtered_data['EXPENDITURE_CATEGORY'] == analysis_category]
        
        if not category_data.empty:
            # Category trend chart
            if selected_department != "All":
                category_trend = category_data.groupby(['FISCAL_YEAR'])['AMOUNT'].sum().reset_index()
                category_trend_fig = px.line(
                    category_trend, x='FISCAL_YEAR', y='AMOUNT',
                    title=f"{analysis_category.title()} Spending Trend - {selected_department}",
                    labels={'AMOUNT': 'Amount ($)', 'FISCAL_YEAR': 'Fiscal Year'},
                    markers=True, color_discrete_sequence=['#1f77b4']
                )
                category_trend_fig.update_traces(line=dict(color='#1f77b4', width=4), marker=dict(color='#1f77b4'))
            else:
                category_trend = category_data.groupby(['DEPARTMENT_NAME', 'FISCAL_YEAR'])['AMOUNT'].sum().reset_index()
                dept_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
                category_trend_fig = px.line(
                    category_trend, x='FISCAL_YEAR', y='AMOUNT', color='DEPARTMENT_NAME',
                    title=f"{analysis_category.title()} Spending Trend by Department",
                    labels={'AMOUNT': 'Amount ($)', 'FISCAL_YEAR': 'Fiscal Year'},
                    markers=True, color_discrete_sequence=dept_colors
                )
            
            category_trend_fig.update_layout(template="plotly_white", plot_bgcolor='white', paper_bgcolor='white')
            category_trend_html = category_trend_fig.to_html(include_plotlyjs=False, div_id="category_trend", config={'displayModeBar': False})
            
            # Monthly seasonality chart
            monthly_pattern = category_data.groupby(['FISCAL_MONTH'])['AMOUNT'].mean().reset_index()
            monthly_pattern['MONTH_NAME'] = monthly_pattern['FISCAL_MONTH'].apply(
                lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][x-1]
            )
            
            seasonality_fig = px.bar(
                monthly_pattern, x='MONTH_NAME', y='AMOUNT',
                title=f"{analysis_category.title()} - Monthly Pattern ({dept_context})",
                labels={'AMOUNT': 'Average Amount ($)', 'MONTH_NAME': 'Month'},
                color_discrete_sequence=['#ff7f0e']
            )
            seasonality_fig.update_traces(marker_color='#ff7f0e')
            seasonality_fig.update_layout(template="plotly_white", plot_bgcolor='white', paper_bgcolor='white')
            seasonality_html = seasonality_fig.to_html(include_plotlyjs=False, div_id="seasonality", config={'displayModeBar': False})
        else:
            category_trend_html = "<p>No data available for category analysis</p>"
            seasonality_html = "<p>No data available for seasonality analysis</p>"

    except Exception as e:
        trend_chart_html = f"<p>Chart generation error: {str(e)}</p>"
        category_chart_html = "<p>Category chart unavailable</p>"
        dept_chart_html = ""
        category_trend_html = "<p>Category trend chart unavailable</p>"
        seasonality_html = "<p>Seasonality chart unavailable</p>"
    
    # Calculate insights for selected category
    category_insights = ""
    if not filtered_data[filtered_data['EXPENDITURE_CATEGORY'] == analysis_category].empty:
        cat_data = filtered_data[filtered_data['EXPENDITURE_CATEGORY'] == analysis_category]
        total_category_spending = cat_data['AMOUNT'].sum()
        avg_monthly_category = cat_data.groupby(['FISCAL_YEAR', 'FISCAL_MONTH'])['AMOUNT'].sum().mean()
        
        if selected_department != "All":
            yearly_totals = cat_data.groupby('FISCAL_YEAR')['AMOUNT'].sum().sort_index()
            insight_details = f"""
            <li><strong>Total {analysis_category.title()} Spending:</strong> {format_currency(total_category_spending)}</li>
            <li><strong>Average Monthly:</strong> {format_currency(avg_monthly_category)}</li>
            <li><strong>Department Focus:</strong> {selected_department}</li>
            """
            
            if len(yearly_totals) > 1:
                latest_year = yearly_totals.index[-1]
                previous_year = yearly_totals.index[-2]
                yoy_growth = ((yearly_totals[latest_year] - yearly_totals[previous_year]) / yearly_totals[previous_year]) * 100
                growth_indicator = "📈" if yoy_growth > 0 else "📉"
                insight_details += f"<li><strong>Year-over-Year Growth ({previous_year} to {latest_year}):</strong> {growth_indicator} {yoy_growth:+.1f}%</li>"
        else:
            top_department = cat_data.groupby('DEPARTMENT_NAME')['AMOUNT'].sum().idxmax()
            top_department_amount = cat_data.groupby('DEPARTMENT_NAME')['AMOUNT'].sum().max()
            insight_details = f"""
            <li><strong>Total {analysis_category.title()} Spending:</strong> {format_currency(total_category_spending)}</li>
            <li><strong>Average Monthly:</strong> {format_currency(avg_monthly_category)}</li>
            <li><strong>Top Department:</strong> {top_department} ({format_currency(top_department_amount)})</li>
            <li><strong>Departments Analyzed:</strong> {len(cat_data['DEPARTMENT_NAME'].unique())}</li>
            """
        
        category_insights = f"""
        <div class="insight-box">
            <h4>💡 {analysis_category.title()} Category Insights:</h4>
            <ul>{insight_details}</ul>
        </div>
        """
    
    # Recent transactions table
    recent_transactions_html = ""
    recent_transactions = filtered_data.sort_values('TRANSACTION_DATE', ascending=False).head(20)
    for _, row in recent_transactions.iterrows():
        director_name = row['DIRECTOR_NAME'] if pd.notna(row['DIRECTOR_NAME']) else 'N/A'
        recent_transactions_html += f"""
        <tr>
            <td>{row['TRANSACTION_DATE']}</td>
            <td>{row['DEPARTMENT_NAME']}</td>
            <td>{row['EXPENDITURE_CATEGORY']}</td>
            <td>{format_currency(row['AMOUNT'])}</td>
            <td>{director_name}</td>
        </tr>
        """
    
    # Complete HTML with all dashboard elements
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Higher Education Finance Dashboard Report</title>
        <meta charset="utf-8">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 20px; 
                line-height: 1.6;
                color: #333;
            }}
            .header {{ 
                background: #1f77b4;
                background: -webkit-linear-gradient(135deg, #1f77b4, #ff7f0e);
                background: linear-gradient(135deg, #1f77b4, #ff7f0e);
                color: white !important; 
                padding: 2rem; 
                border-radius: 15px; 
                text-align: center; 
                margin: 2rem 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                -webkit-print-color-adjust: exact !important;
                color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}
            .header h1, .header h2, .header p {{
                color: white !important;
                margin: 10px 0;
            }}
            .header h1 {{
                font-size: 2.5rem;
                font-weight: bold;
                margin: 0 0 1rem 0;
            }}
            .header h2 {{
                font-size: 1.2rem;
                margin: 0 0 1.5rem 0;
                opacity: 0.9;
            }}
            .header-details {{
                background: rgba(255,255,255,0.1);
                padding: 1rem;
                border-radius: 10px;
                margin-top: 1.5rem;
            }}
            .header-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
                text-align: left;
            }}
            .header-grid div {{
                color: white;
            }}
            .metrics-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
                margin: 30px 0; 
            }}
            .metric-box {{ 
                background: #f8f9fa; 
                padding: 20px; 
                border-radius: 10px; 
                border-left: 5px solid #1f77b4;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }}
            .metric-value {{ 
                font-size: 2em; 
                font-weight: bold; 
                color: #1f77b4; 
                margin: 10px 0;
            }}
            .chart-section {{ 
                margin: 40px 0; 
                page-break-inside: avoid;
            }}
            .chart-grid {{ 
                display: grid; 
                grid-template-columns: 1fr 1fr; 
                gap: 30px; 
                margin: 20px 0;
            }}
            .insight-box {{
                background: #e3f2fd;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                border-left: 5px solid #2196f3;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin: 20px 0; 
                background: white;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }}
            th, td {{ 
                border: 1px solid #ddd; 
                padding: 12px; 
                text-align: left; 
            }}
            th {{ 
                background: #f8f9fa;
                font-weight: bold;
                color: #495057;
            }}
            .section-title {{
                color: #1f77b4;
                border-bottom: 2px solid #1f77b4;
                padding-bottom: 10px;
                margin-top: 40px;
            }}
            .footer {{ 
                text-align: center; 
                margin-top: 50px; 
                padding: 20px;
                color: #666; 
                font-size: 14px; 
                border-top: 1px solid #eee;
            }}
            @media print {{
                body {{ margin: 0; }}
                .chart-section {{ page-break-inside: avoid; }}
                .header {{
                    background: #1f77b4 !important;
                    -webkit-print-color-adjust: exact !important;
                }}
                .header * {{
                    color: white !important;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 Higher Education Finance Dashboard</h1>
            <h2>Complete Financial Analysis Report</h2>
            
            <div class="header-details">
                <div class="header-grid">
                    <div>
                        <strong>👤 User:</strong><br>
                        {current_user}
                    </div>
                    <div>
                        <strong>🏢 Department Focus:</strong><br>
                        {dept_context}
                    </div>
                    <div>
                        <strong>📅 Analysis Period:</strong><br>
                        {years_context}
                    </div>
                    <div>
                        <strong>🏷️ Category Filter:</strong><br>
                        {categories_context}
                    </div>
                </div>
                <p style="margin-top: 1rem; text-align: center;"><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
        </div>
        
        <h2 class="section-title">📊 Key Performance Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-box">
                <h4>💰 Total Spending</h4>
                <div class="metric-value">{format_currency(total_spending)}</div>
            </div>
            <div class="metric-box">
                <h4>📅 Average Monthly</h4>
                <div class="metric-value">{format_currency(avg_monthly)}</div>
            </div>
            <div class="metric-box">
                <h4>🧾 Transactions</h4>
                <div class="metric-value">{transaction_count:,}</div>
            </div>
            <div class="metric-box">
                <h4>📊 Categories</h4>
                <div class="metric-value">{unique_categories}</div>
            </div>
        </div>
        
        <h2 class="section-title">📈 Financial Analysis Charts</h2>
        <div class="chart-grid">
            <div class="chart-section">
                <h3>💹 Spending Trend Over Time</h3>
                {trend_chart_html}
            </div>
            <div class="chart-section">
                <h3>🥧 Category Breakdown</h3>
                {category_chart_html}
            </div>
        </div>
        
        {dept_chart_html}
        
        <h2 class="section-title">🔍 Category Deep Dive: {analysis_category.title()} - {dept_context}</h2>
        <div class="chart-grid">
            <div class="chart-section">
                <h3>📊 Department Comparison</h3>
                {category_trend_html}
            </div>
            <div class="chart-section">
                <h3>📅 Monthly Seasonality</h3>
                {seasonality_html}
            </div>
        </div>
        
        {category_insights}
        
        <h2 class="section-title">📋 Recent Transaction Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Department</th>
                    <th>Category</th>
                    <th>Amount</th>
                    <th>Director</th>
                </tr>
            </thead>
            <tbody>
                {recent_transactions_html}
            </tbody>
        </table>
        
        <div class="footer">
            <p><strong>Higher Education Finance Dashboard</strong> | Row Access Policy Demo</p>
            <p>Built with Streamlit in Snowflake | Data filtered by user permissions</p>
            <p>This comprehensive report includes {transaction_count:,} transactions with row-level security applied for user: <strong>{current_user}</strong></p>
            <p>Report generated from filtered dataset: {dept_context} | {years_context}</p>
        </div>
    </body>
    </html>
    """
    
    return html_content

def main():
    """Main Streamlit application"""
    
    # Header with custom styling
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1f77b4 0%, #ff7f0e 100%);
        background: -webkit-linear-gradient(135deg, #1f77b4, #ff7f0e);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    ">
        <h1 style="margin: 0 0 1rem 0; font-size: 3rem; font-weight: bold; color: white;">
            🎓 Higher Education Finance Dashboard
        </h1>
        <p style="margin: 0; font-size: 1.3rem; opacity: 0.9; color: white;">
            Row Access Policy Demo - Department Financial Analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get current user and access info
    current_user = get_current_user()
    user_access = get_user_access_info(current_user)
    
    # Display user context in sidebar
    with st.sidebar:
        st.header("👤 User Context")
        st.write(f"**Current User:** {current_user}")
        
        if not user_access.empty:
            # Get all department access for current user
            user_departments = user_access['DEPARTMENT_NAME'].dropna().tolist()
            access_level = user_access.iloc[0]['ACCESS_LEVEL']
            
            st.write(f"**Access Type:** {access_level}")
            
            if len(user_departments) > 1:
                # User has access to multiple departments (like ADMIN)
                st.write(f"**Departments Accessible:** {len(user_departments)} departments")
                st.success("🔓 You have access to multiple departments:")
                for dept in sorted(user_departments):
                    st.write(f"   • {dept}")
            elif len(user_departments) == 1:
                # User has access to single department (like MARKETING_DIRECTOR)
                dept_name = user_departments[0]
                st.write(f"**Department Access:** {dept_name}")
                st.info(f"🔒 You can only view {dept_name} department data due to row access policies.")
            else:
                st.warning("⚠️ No department access found.")
        else:
            st.warning("⚠️ No access permissions found for current user.")
        
        st.markdown("---")
        st.markdown("**🛡️ Row Access Policy Details:**")
        st.markdown("""
        This demo uses **department-based row access control**:
        
        **Current Implementation:**
        - Row Access Policy applied to USER_ENTITLEMENTS table
        - Users get individual department access records
        - Data visibility determined by entitlement records
        
        **User Types:**
        - **Admin Users**: Multiple department access records  
          → Can see all departments
        - **Department Users**: Single department access record  
          → Can only see their department's data
          
        **How it Works:**
        1. Each user has entitlement record(s) in USER_ENTITLEMENTS
        2. Row Access Policy filters data by current username
        3. Users only see data for departments they have access to
        4. Streamlit app automatically applies these restrictions
        """)
        
        st.markdown("---")
        st.markdown("**📊 Demo Scenario:**")
        if current_user == 'ADMIN':
            st.markdown("""
            **ADMIN User Experience:**
            - ✅ Access records for ALL departments
            - ✅ Can view complete university financial picture
            - ✅ See cross-departmental comparisons
            - ✅ Full dashboard functionality
            """)
        elif current_user == 'MARKETING_DIRECTOR':
            st.markdown("""
            **MARKETING_DIRECTOR Experience:**
            - ✅ Access record for Marketing department only
            - 🔒 Cannot see other departments' data
            - 📊 Marketing-focused analytics and insights
            - 💡 Discovers software subscription spending increase
            """)
        else:
            st.markdown(f"""
            **{current_user} Experience:**
            - Access determined by entitlement records
            - Data filtered automatically by row access policy
            - Dashboard adapts to user's department visibility
            """)
    
    # Load data
    with st.spinner("Loading financial data..."):
        finance_data = load_finance_data()
        finance_summary = load_finance_summary()

    if finance_data.empty:
        st.error("No financial data available for your user permissions.")
        st.stop()

    # Get available options for filters
    departments = sorted(finance_data['DEPARTMENT_NAME'].unique())
    years = sorted(finance_data['FISCAL_YEAR'].unique())
    categories = sorted(finance_data['EXPENDITURE_CATEGORY'].unique())

    # Filters in main area
    st.markdown("### 🎯 Filters")
    col1, col2, col3 = st.columns(3)

    with col1:
        # Add select all/deselect all buttons for years
        available_years = sorted(finance_data['FISCAL_YEAR'].unique())
        
        # Buttons for year selection
        year_col1, year_col2 = st.columns(2)
        with year_col1:
            if st.button("Select All Years", key="select_all_years"):
                st.session_state.selected_years = available_years
        with year_col2:
            if st.button("Deselect All Years", key="deselect_all_years"):
                st.session_state.selected_years = []
        
        # Initialize session state if not exists
        if 'selected_years' not in st.session_state:
            st.session_state.selected_years = available_years
        
        selected_years = st.multiselect(
            "Select Fiscal Year(s)",
            available_years,
            default=st.session_state.selected_years,
            key="years_multiselect"
        )
        
        # Update session state
        st.session_state.selected_years = selected_years

    with col2:
        # Add select all/deselect all buttons for categories
        available_categories = sorted(finance_data['EXPENDITURE_CATEGORY'].unique())
        
        # Buttons for category selection
        cat_col1, cat_col2 = st.columns(2)
        with cat_col1:
            if st.button("Select All Categories", key="select_all_categories"):
                st.session_state.selected_categories = available_categories
        with cat_col2:
            if st.button("Deselect All Categories", key="deselect_all_categories"):
                st.session_state.selected_categories = []
        
        # Initialize session state if not exists
        if 'selected_categories' not in st.session_state:
            st.session_state.selected_categories = available_categories
        
        selected_categories = st.multiselect(
            "Select Expenditure Category(s)",
            available_categories,
            default=st.session_state.selected_categories,
            key="categories_multiselect"
        )
        
        # Update session state
        st.session_state.selected_categories = selected_categories

    with col3:
        selected_department = st.selectbox(
            "Select Department",
            ["All"] + departments,
            index=0
        )

    # Apply filters
    filtered_data = finance_data.copy()

    if selected_years:
        filtered_data = filtered_data[filtered_data['FISCAL_YEAR'].isin(selected_years)]

    if selected_categories:
        filtered_data = filtered_data[filtered_data['EXPENDITURE_CATEGORY'].isin(selected_categories)]

    if selected_department != "All":
        filtered_data = filtered_data[filtered_data['DEPARTMENT_NAME'] == selected_department]
    
    # Validate that at least one year and category is selected
    if not selected_years:
        st.warning("⚠️ Please select at least one fiscal year to view data.")
        st.stop()

    if not selected_categories:
        st.warning("⚠️ Please select at least one expenditure category to view data.")
        st.stop()

    if filtered_data.empty:
        st.error("No data available for the selected filters. Please adjust your selections.")
        st.stop()

    # Combined Department Display and Data Overview
    departments_display = [selected_department] if selected_department != "All" else departments
    years_display = selected_years if selected_years else ["No years selected"]

    if selected_department != "All":
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            background: -webkit-linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin: 2rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            <h2 style="margin: 0 0 1rem 0; font-size: 2.5rem; font-weight: bold; color: white;">
                🏢 {selected_department} Department
            </h2>
            <p style="margin: 0 0 1.5rem 0; font-size: 1.2rem; opacity: 0.9; color: white;">
                Financial Analysis Dashboard
            </p>
            <div style="
                background: rgba(255,255,255,0.1);
                padding: 1rem;
                border-radius: 10px;
                backdrop-filter: blur(10px);
            ">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; text-align: left;">
                    <div style="color: white;">
                        <strong>📊 Department Focus:</strong><br>
                        {selected_department}
                    </div>
                    <div style="color: white;">
                        <strong>📅 Years Analyzed:</strong><br>
                        {', '.join(map(str, sorted(years_display)))}
                    </div>
                    <div style="color: white;">
                        <strong>📈 Records Shown:</strong><br>
                        {len(filtered_data):,} transactions
                    </div>
                    <div style="color: white;">
                        <strong>🏷️ Categories Available:</strong><br>
                        {len(categories)} expenditure types
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1f77b4 0%, #ff7f0e 100%);
            background: -webkit-linear-gradient(135deg, #1f77b4, #ff7f0e);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            margin: 2rem 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            <h2 style="margin: 0 0 1rem 0; font-size: 2.5rem; font-weight: bold; color: white;">
                🎓 All Departments
            </h2>
            <p style="margin: 0 0 1.5rem 0; font-size: 1.2rem; opacity: 0.9; color: white;">
                University-Wide Financial Analysis
            </p>
            <div style="
                background: rgba(255,255,255,0.1);
                padding: 1rem;
                border-radius: 10px;
                backdrop-filter: blur(10px);
            ">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; text-align: left;">
                    <div style="color: white;">
                        <strong>🏢 Departments Visible:</strong><br>
                        {', '.join(departments_display)}
                    </div>
                    <div style="color: white;">
                        <strong>📅 Years Analyzed:</strong><br>
                        {', '.join(map(str, sorted(years_display)))}
                    </div>
                    <div style="color: white;">
                        <strong>📈 Records Shown:</strong><br>
                        {len(filtered_data):,} transactions
                    </div>
                    <div style="color: white;">
                        <strong>🏷️ Categories Available:</strong><br>
                        {len(categories)} expenditure types
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Key Metrics
    st.markdown("### 📈 Key Metrics")
    
    if not filtered_data.empty:
        total_spending = filtered_data['AMOUNT'].sum()
        avg_monthly = filtered_data.groupby(['FISCAL_YEAR', 'FISCAL_MONTH'])['AMOUNT'].sum().mean()
        transaction_count = len(filtered_data)
        unique_categories = filtered_data['EXPENDITURE_CATEGORY'].nunique()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <h4>💰 Total Spending</h4>
                <h2>{format_currency(total_spending)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <h4>📅 Avg Monthly</h4>
                <h2>{format_currency(avg_monthly)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-container">
                <h4>🧾 Transactions</h4>
                <h2>{transaction_count:,}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-container">
                <h4>📊 Categories</h4>
                <h2>{unique_categories}</h2>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts Section
    st.markdown("### 📊 Financial Analysis")
    
    # Two column layout for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            create_trend_chart(filtered_data, selected_categories),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            create_category_breakdown(filtered_data, selected_years),
            use_container_width=True
        )
    
    # Department comparison (only show if user can see multiple departments)
    if len(departments) > 1:
        st.plotly_chart(
            create_department_comparison(filtered_data),
            use_container_width=True
        )
    
    # Dynamic Category Analysis
    dept_context_display = selected_department if selected_department != "All" else "All Departments"

    st.markdown(f"### 📊 Category Deep Dive - {dept_context_display}")
    st.markdown(f"*Explore spending patterns for any expenditure category across {dept_context_display.lower()} and time*")

    # Filter analysis_category options to only show selected categories
    available_analysis_categories = [cat for cat in categories if cat in selected_categories] if selected_categories else categories

    # Add category selector for analysis
    analysis_category = st.selectbox(
        "Select category to analyze:",
        available_analysis_categories,
        index=available_analysis_categories.index('software subscriptions') if 'software subscriptions' in available_analysis_categories else 0,
        key="analysis_category"
    )

    # Use filtered_data instead of finance_data to respect department selection
    category_data = filtered_data[filtered_data['EXPENDITURE_CATEGORY'] == analysis_category]

    if not category_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Trend by department for selected category (filtered by selected department)
            if selected_department != "All":
                # If specific department selected, show year-over-year trend for that department
                category_trend = category_data.groupby(['FISCAL_YEAR'])['AMOUNT'].sum().reset_index()
                
                fig_category_trend = px.line(
                    category_trend,
                    x='FISCAL_YEAR',
                    y='AMOUNT',
                    title=f"{analysis_category.title()} Spending Trend - {selected_department}",
                    labels={'AMOUNT': 'Amount ($)', 'FISCAL_YEAR': 'Fiscal Year'},
                    markers=True,
                    color_discrete_sequence=['#1f77b4']
                )
                fig_category_trend.update_traces(
                    line=dict(color='#1f77b4', width=4), 
                    marker=dict(size=8, color='#1f77b4')
                )
            else:
                # If all departments, show comparison across departments
                category_trend = category_data.groupby(['DEPARTMENT_NAME', 'FISCAL_YEAR'])['AMOUNT'].sum().reset_index()
                
                # Use consistent department colors
                dept_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
                
                fig_category_trend = px.line(
                    category_trend,
                    x='FISCAL_YEAR',
                    y='AMOUNT',
                    color='DEPARTMENT_NAME',
                    title=f"{analysis_category.title()} Spending Trend by Department",
                    labels={'AMOUNT': 'Amount ($)', 'FISCAL_YEAR': 'Fiscal Year'},
                    markers=True,
                    color_discrete_sequence=dept_colors
                )
            
            fig_category_trend.update_layout(
                xaxis_title="Fiscal Year",
                yaxis_title="Amount ($)",
                template="plotly_white",
                legend_title="Department" if selected_department == "All" else None,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig_category_trend, use_container_width=True)
        
        with col2:
            # Monthly seasonality for selected category (filtered by selected department)
            monthly_pattern = category_data.groupby(['FISCAL_MONTH'])['AMOUNT'].mean().reset_index()
            monthly_pattern['MONTH_NAME'] = monthly_pattern['FISCAL_MONTH'].apply(
                lambda x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][x-1]
            )
            
            fig_seasonality = px.bar(
                monthly_pattern,
                x='MONTH_NAME',
                y='AMOUNT',
                title=f"{analysis_category.title()} - Monthly Pattern ({dept_context_display})",
                labels={'AMOUNT': 'Average Amount ($)', 'MONTH_NAME': 'Month'},
                color_discrete_sequence=['#ff7f0e']
            )
            
            # Ensure bar colors are set explicitly
            fig_seasonality.update_traces(marker_color='#ff7f0e')
            
            fig_seasonality.update_layout(
                xaxis_title="Month",
                yaxis_title="Average Amount ($)",
                template="plotly_white",
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            st.plotly_chart(fig_seasonality, use_container_width=True)
        
        # Summary insights for selected category (filtered by selected department)
        total_category_spending = category_data['AMOUNT'].sum()
        avg_monthly_spending = category_data.groupby(['FISCAL_YEAR', 'FISCAL_MONTH'])['AMOUNT'].sum().mean()
        
        # Calculate insights based on department selection
        if selected_department != "All":
            # For specific department, show year-over-year growth
            yearly_totals = category_data.groupby('FISCAL_YEAR')['AMOUNT'].sum().sort_index()
            insight_details = f"""
            - **Total {analysis_category.title()} Spending**: {format_currency(total_category_spending)}
            - **Average Monthly**: {format_currency(avg_monthly_spending)}
            - **Department Focus**: {selected_department}
            """
            
            if len(yearly_totals) > 1:
                latest_year = yearly_totals.index[-1]
                previous_year = yearly_totals.index[-2]
                yoy_growth = ((yearly_totals[latest_year] - yearly_totals[previous_year]) / yearly_totals[previous_year]) * 100
                growth_color = "🔴" if yoy_growth > 15 else "🟡" if yoy_growth > 5 else "🟢"
                insight_details += f"\n        - **Year-over-Year Growth ({previous_year} to {latest_year})**: {growth_color} {yoy_growth:+.1f}%"
        else:
            # For all departments, show top department
            top_department = category_data.groupby('DEPARTMENT_NAME')['AMOUNT'].sum().idxmax()
            top_department_amount = category_data.groupby('DEPARTMENT_NAME')['AMOUNT'].sum().max()
            
            insight_details = f"""
            - **Total {analysis_category.title()} Spending**: {format_currency(total_category_spending)}
            - **Average Monthly**: {format_currency(avg_monthly_spending)}
            - **Top Department**: {top_department} ({format_currency(top_department_amount)})
            - **Departments Analyzed**: {len(category_data['DEPARTMENT_NAME'].unique())}
            """
        
        st.info(f"""
        **💡 {analysis_category.title()} Insights for {dept_context_display}:**
        {insight_details}
        """)

    else:
        st.warning(f"No data available for {analysis_category} in {dept_context_display}")
    
    # Show insight for marketing users
    if current_user == 'MARKETING_DIRECTOR' or 'Marketing' in departments:
        marketing_software = finance_data[
            (finance_data['DEPARTMENT_NAME'] == 'Marketing') & 
            (finance_data['EXPENDITURE_CATEGORY'] == 'software subscriptions')
        ]
        
        if not marketing_software.empty:
            recent_spending = marketing_software[marketing_software['FISCAL_YEAR'] >= 2023]['AMOUNT'].sum()
            earlier_spending = marketing_software[marketing_software['FISCAL_YEAR'] < 2023]['AMOUNT'].mean() * 2  # 2 years
            
            if recent_spending > earlier_spending:
                increase_pct = ((recent_spending - earlier_spending) / earlier_spending) * 100
                st.warning(f"""
                **💡 Insight:** Marketing software subscriptions have increased by {increase_pct:.1f}% 
                since 2023. Consider leveraging central IT services to optimize costs.
                """)
    
    # Detailed Data Table
    if selected_department != "All":
        st.markdown(f"### 📋 Detailed Transaction Data - {selected_department} Department")
        st.markdown(f"*Showing {len(filtered_data):,} transactions for {selected_department} department*")
    else:
        st.markdown("### 📋 Detailed Transaction Data - All Departments")
        st.markdown(f"*Showing {len(filtered_data):,} transactions across all departments*")
    
    # Display options
    col1, col2 = st.columns(2)
    with col1:
        show_records = st.selectbox("Records to display", [50, 100, 500, "All"])
    with col2:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Amount (Highest)", "Amount (Lowest)"])
    
    # Apply sorting
    if sort_by == "Date (Newest)":
        display_data = filtered_data.sort_values('TRANSACTION_DATE', ascending=False)
    elif sort_by == "Date (Oldest)":
        display_data = filtered_data.sort_values('TRANSACTION_DATE', ascending=True)
    elif sort_by == "Amount (Highest)":
        display_data = filtered_data.sort_values('AMOUNT', ascending=False)
    else:  # Amount (Lowest)
        display_data = filtered_data.sort_values('AMOUNT', ascending=True)
    
    # Limit records
    if show_records != "All":
        display_data = display_data.head(show_records)
    
    # Format the data for display
    display_data_formatted = display_data.copy()
    display_data_formatted['AMOUNT'] = display_data_formatted['AMOUNT'].apply(format_currency)
    display_data_formatted['TRANSACTION_DATE'] = pd.to_datetime(display_data_formatted['TRANSACTION_DATE']).dt.strftime('%Y-%m-%d')
    
    # Select columns for display
    columns_to_show = [
        'DEPARTMENT_NAME', 'TRANSACTION_DATE', 'EXPENDITURE_CATEGORY', 
        'AMOUNT', 'DIRECTOR_NAME', 'FISCAL_YEAR'
    ]
    
    st.dataframe(
        display_data_formatted[columns_to_show],
        use_container_width=True,
        hide_index=True
    )
    
    # Download options
    st.markdown("### 📥 Download Options")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 Download Data as CSV"):
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="Download CSV Data",
                data=csv,
                file_name=f"finance_data_{current_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    with col2:
        if st.button("📄 Download Complete Dashboard"):
            with st.spinner("Generating comprehensive dashboard report..."):
                try:
                    # Generate complete HTML report with all charts and data
                    complete_html = generate_complete_dashboard_html(
                        current_user, 
                        filtered_data,
                        finance_data,
                        selected_department, 
                        selected_years, 
                        selected_categories,
                        analysis_category
                    )
                    
                    st.download_button(
                        label="Download Full Dashboard Report",
                        data=complete_html,
                        file_name=f"complete_dashboard_{current_user}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
                    
                    st.success("✅ Dashboard report generated successfully!")
                    st.info("💡 **How to convert to PDF:**\n1. Download the HTML file\n2. Open it in Chrome/Firefox\n3. Press Ctrl+P (Cmd+P on Mac)\n4. Choose 'Save as PDF'\n5. Adjust settings for best quality")
                    
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")
                    st.info("Fallback: Try the basic CSV download instead.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p><strong>Higher Education Finance Dashboard</strong> | Row Access Policy Demo</p>
        <p>Built with Streamlit in Snowflake | Data filtered by user permissions</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
