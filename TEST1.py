import streamlit as st
import pandas as pd
import numpy as np
from numpy import log, sqrt, exp
import requests
from bs4 import BeautifulSoup
import re
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import io
import base64

# Page configuration
try:
    st.set_page_config(
        page_title="DCF Valuation Tool - Investment Banking Edition",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except st.errors.StreamlitAPIException:
    pass

# Enhanced Industry benchmarks with more comprehensive data
INDUSTRY_BENCHMARKS = {
    "Technology": {
        "ebitda_margin": 25.0, "capex_rev": 5.0, "depreciation_rev": 4.0, "wc_change_rev": 2.0, 
        "beta": 1.3, "debt_equity": 0.15, "roe": 18.0, "roic": 15.0, "revenue_multiple": 8.5,
        "typical_growth_high": 25.0, "typical_growth_mature": 5.0
    },
    "Healthcare": {
        "ebitda_margin": 22.0, "capex_rev": 8.0, "depreciation_rev": 6.0, "wc_change_rev": 3.0, 
        "beta": 0.9, "debt_equity": 0.25, "roe": 14.0, "roic": 12.0, "revenue_multiple": 6.0,
        "typical_growth_high": 15.0, "typical_growth_mature": 4.0
    },
    "Consumer Goods": {
        "ebitda_margin": 18.0, "capex_rev": 6.0, "depreciation_rev": 5.0, "wc_change_rev": 4.0, 
        "beta": 1.1, "debt_equity": 0.35, "roe": 13.0, "roic": 11.0, "revenue_multiple": 3.5,
        "typical_growth_high": 12.0, "typical_growth_mature": 3.5
    },
    "Financial Services": {
        "ebitda_margin": 35.0, "capex_rev": 2.0, "depreciation_rev": 2.0, "wc_change_rev": 1.0, 
        "beta": 1.2, "debt_equity": 0.80, "roe": 12.0, "roic": 10.0, "revenue_multiple": 2.8,
        "typical_growth_high": 10.0, "typical_growth_mature": 3.0
    },
    "Manufacturing": {
        "ebitda_margin": 15.0, "capex_rev": 7.0, "depreciation_rev": 6.0, "wc_change_rev": 3.5, 
        "beta": 1.0, "debt_equity": 0.45, "roe": 11.0, "roic": 9.0, "revenue_multiple": 2.2,
        "typical_growth_high": 8.0, "typical_growth_mature": 2.5
    },
    "Energy": {
        "ebitda_margin": 20.0, "capex_rev": 12.0, "depreciation_rev": 10.0, "wc_change_rev": 2.0, 
        "beta": 1.4, "debt_equity": 0.40, "roe": 10.0, "roic": 8.0, "revenue_multiple": 1.8,
        "typical_growth_high": 6.0, "typical_growth_mature": 2.0
    },
    "Real Estate": {
        "ebitda_margin": 30.0, "capex_rev": 15.0, "depreciation_rev": 8.0, "wc_change_rev": 1.5, 
        "beta": 0.8, "debt_equity": 0.65, "roe": 9.0, "roic": 7.0, "revenue_multiple": 4.2,
        "typical_growth_high": 7.0, "typical_growth_mature": 2.5
    },
    "Retail": {
        "ebitda_margin": 12.0, "capex_rev": 4.0, "depreciation_rev": 3.0, "wc_change_rev": 5.0, 
        "beta": 1.1, "debt_equity": 0.30, "roe": 14.0, "roic": 12.0, "revenue_multiple": 1.5,
        "typical_growth_high": 9.0, "typical_growth_mature": 2.5
    },
    "Telecommunications": {
        "ebitda_margin": 28.0, "capex_rev": 18.0, "depreciation_rev": 15.0, "wc_change_rev": 2.0, 
        "beta": 0.9, "debt_equity": 0.55, "roe": 8.0, "roic": 6.0, "revenue_multiple": 2.5,
        "typical_growth_high": 5.0, "typical_growth_mature": 2.0
    },
    "Utilities": {
        "ebitda_margin": 25.0, "capex_rev": 10.0, "depreciation_rev": 8.0, "wc_change_rev": 1.0, 
        "beta": 0.7, "debt_equity": 0.70, "roe": 7.0, "roic": 5.0, "revenue_multiple": 3.0,
        "typical_growth_high": 4.0, "typical_growth_mature": 2.0
    }
}

# Enhanced CSS for professional investment banking look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    .metric-card {
        background: linear-gradient(145deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin: 0.75rem 0;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    .executive-summary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    
    .valuation-highlight {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 1rem 0;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .recommendation-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        text-align: center;
        box-shadow: 0 15px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    .risk-analysis {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: #333;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    .professional-table {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .header-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 3rem 0;
        text-align: center;
        margin-bottom: 2rem;
        border-radius: 0 0 30px 30px;
    }
    
    .flip-card-container {
        perspective: 1000px;
        margin-bottom: 2rem;
    }
    
    .flip-card {
        width: 100%;
        height: 280px;
        background-color: transparent;
        perspective: 1000px;
    }
    
    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: center;
        transition: transform 0.8s;
        transform-style: preserve-3d;
    }
    
    .flip-card:hover .flip-card-inner {
        transform: rotateY(180deg);
    }
    
    .flip-card-front, .flip-card-back {
        position: absolute;
        width: 100%;
        height: 100%;
        backface-visibility: hidden;
        border-radius: 15px;
        padding: 2rem;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    
    .flip-card-front {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    .flip-card-back {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        transform: rotateY(180deg);
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    .section-divider {
        height: 3px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 2px;
        margin: 3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Enhanced risk-free rate fetching with more robust error handling
@st.cache_data(ttl=3600)
def get_risk_free_rate(country):
    """Enhanced risk-free rate fetching with multiple fallback sources"""
    try:
        country_urls = {
            "India": "https://tradingeconomics.com/india/government-bond-yield",
            "USA": "https://tradingeconomics.com/united-states/government-bond-yield", 
            "UK": "https://tradingeconomics.com/united-kingdom/government-bond-yield",
            "Germany": "https://tradingeconomics.com/germany/government-bond-yield",
            "France": "https://tradingeconomics.com/france/government-bond-yield"
        }
        
        if country not in country_urls:
            return 6.0
            
        url = country_urls[country]
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        rate_element = soup.find('span', {'id': 'p_cur_val'}) or soup.find('div', {'class': 'col-xs-6 col-sm-4 col-md-4 col-lg-3'})
        
        if rate_element:
            rate_text = rate_element.get_text().strip()
            rate_match = re.search(r'(\d+\.?\d*)', rate_text)
            if rate_match:
                return float(rate_match.group(1))
        
        # Enhanced fallback rates (updated as of 2025)
        fallback_rates = {
            "India": 6.85, "USA": 4.25, "UK": 4.15, "Germany": 2.35, "France": 2.95
        }
        return fallback_rates.get(country, 6.0)
        
    except Exception as e:
        st.warning(f"Could not fetch live rate for {country}. Using estimated rate.")
        fallback_rates = {
            "India": 6.85, "USA": 4.25, "UK": 4.15, "Germany": 2.35, "France": 2.95
        }
        return fallback_rates.get(country, 6.0)

def calculate_financial_ratios(revenue, ebitda, fcf, capex, shares_outstanding):
    """Calculate comprehensive financial ratios for analysis"""
    ratios = {}
    
    if len(revenue) > 0:
        # Growth metrics
        ratios['revenue_cagr'] = (revenue[-1] / revenue[0]) ** (1/len(revenue)) - 1 if len(revenue) > 1 else 0
        
        # Profitability metrics
        ratios['avg_ebitda_margin'] = np.mean([e/r for e, r in zip(ebitda, revenue) if r > 0])
        ratios['avg_fcf_margin'] = np.mean([f/r for f, r in zip(fcf, revenue) if r > 0])
        
        # Efficiency metrics
        ratios['avg_capex_intensity'] = np.mean([c/r for c, r in zip(capex, revenue) if r > 0])
        
        # Per share metrics
        if shares_outstanding > 0:
            ratios['fcf_per_share'] = fcf[-1] / shares_outstanding if fcf else 0
            ratios['revenue_per_share'] = revenue[-1] / shares_outstanding if revenue else 0
    
    return ratios

def determine_risk_level(beta, industry, debt_ratio, fcf_volatility):
    """Determine investment risk level based on multiple factors"""
    risk_score = 0
    
    # Beta contribution
    if beta > 1.5:
        risk_score += 3
    elif beta > 1.2:
        risk_score += 2
    elif beta > 0.8:
        risk_score += 1
    
    # Industry risk
    high_risk_industries = ["Technology", "Energy", "Real Estate"]
    if industry in high_risk_industries:
        risk_score += 2
    
    # Debt level
    if debt_ratio > 50:
        risk_score += 2
    elif debt_ratio > 30:
        risk_score += 1
    
    # FCF volatility (simplified)
    if fcf_volatility > 0.3:
        risk_score += 2
    elif fcf_volatility > 0.15:
        risk_score += 1
    
    # Risk classification
    if risk_score >= 7:
        return "🔴 Very High Risk", "#dc2626"
    elif risk_score >= 5:
        return "🟠 High Risk", "#ea580c"
    elif risk_score >= 3:
        return "🟡 Moderate Risk", "#ca8a04"
    else:
        return "🟢 Low Risk", "#16a34a"

def format_currency(value, symbol):
    """Enhanced currency formatting with better precision"""
    abs_value = abs(value)
    if abs_value >= 1e12:
        return f"{symbol}{value/1e12:.2f}T"
    elif abs_value >= 1e9:
        return f"{symbol}{value/1e9:.2f}B"
    elif abs_value >= 1e6:
        return f"{symbol}{value/1e6:.2f}M"
    elif abs_value >= 1e3:
        return f"{symbol}{value/1e3:.2f}K"
    else:
        return f"{symbol}{value:.0f}"

def generate_investment_thesis(company_name, industry, ratios, valuation_results, recommendation):
    """Generate a comprehensive investment thesis"""
    
    current_date = datetime.now().strftime("%B %d, %Y")
    
    thesis = f"""
# 🏛️ INVESTMENT THESIS & VALUATION REPORT

**Company:** {company_name}  
**Sector:** {industry}  
**Report Date:** {current_date}  
**Analyst:** DCF Valuation Model  

---

## 📊 EXECUTIVE SUMMARY

{company_name} operates in the {industry.lower()} sector and presents {'an attractive' if 'BUY' in recommendation else 'a challenging'} investment opportunity based on our comprehensive DCF analysis.

### Key Investment Highlights:
- **Revenue Growth:** {ratios.get('revenue_cagr', 0)*100:.1f}% CAGR projected
- **Profitability:** {ratios.get('avg_ebitda_margin', 0)*100:.1f}% average EBITDA margin
- **Cash Generation:** {ratios.get('avg_fcf_margin', 0)*100:.1f}% average FCF margin
- **Capital Efficiency:** {ratios.get('avg_capex_intensity', 0)*100:.1f}% CapEx intensity

---

## 🎯 VALUATION SUMMARY

Our Monte Carlo DCF analysis yields the following intrinsic value estimates:

| Scenario | Valuation | Probability |
|----------|-----------|-------------|
| Bear Case | {valuation_results.get('bear', 'N/A')} | 25% |
| Base Case | {valuation_results.get('base', 'N/A')} | 50% |
| Bull Case | {valuation_results.get('bull', 'N/A')} | 25% |

**Weighted Average Fair Value:** {valuation_results.get('weighted_avg', 'N/A')}

---

## 🔍 INVESTMENT RATIONALE

### Strengths:
- Strong market position in {industry.lower()} sector
- Consistent cash flow generation capabilities
- Reasonable capital allocation efficiency

### Risk Factors:
- Industry cyclicality and competitive pressures
- Macroeconomic sensitivity
- Execution risks in growth initiatives

---

## 📈 RECOMMENDATION: {recommendation}

Based on our analysis, we recommend a **{recommendation}** rating for {company_name}.

*This analysis is for educational purposes only and should not be considered as investment advice.*
    """
    
    return thesis

# Professional Header
st.markdown("""
<div class="header-banner">
    <h1 style='font-size: 3rem; margin-bottom: 0.5rem; font-weight: 700;'>💰  Comprehensive Valuation Model</h1>
    <p style='font-size: 1.3rem; opacity: 0.9; margin: 0;'>Professional-Grade Cash Flow Valuation Platform</p>
    <div style='width: 100px; height: 4px; background: rgba(255,255,255,0.3); margin: 1.5rem auto; border-radius: 2px;'></div>
</div>
""", unsafe_allow_html=True)

# Enhanced Help Section with Professional Flip Cards
st.markdown("### 📚 Professional Valuation Framework")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="flip-card-container">
        <div class="flip-card">
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <div style='font-size: 3rem; margin-bottom: 1rem;'>📊</div>
                    <h3>Financial Statement Analysis</h3>
                    <p>Core Fundamentals</p>
                </div>
                <div class="flip-card-back">
                    <h4>Key Components:</h4>
                    <p><strong>Revenue:</strong> Top-line growth driver<br>
                    <strong>EBITDA:</strong> Operating cash generation<br>
                    <strong>Margins:</strong> Profitability efficiency<br>
                    <strong>Growth Rates:</strong> Expansion trajectory</p>
                    <p><em>Source: Income Statement & Cash Flow Statement</em></p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="flip-card-container">
        <div class="flip-card">
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <div style='font-size: 3rem; margin-bottom: 1rem;'>🏗️</div>
                    <h3>Capital Allocation</h3>
                    <p>Investment Efficiency</p>
                </div>
                <div class="flip-card-back">
                    <h4>Critical Metrics:</h4>
                    <p><strong>CapEx:</strong> Growth investments<br>
                    <strong>Working Capital:</strong> Operational efficiency<br>
                    <strong>ROIC:</strong> Return on invested capital<br>
                    <strong>Free Cash Flow:</strong> Value creation</p>
                    <p><em>Indicates management's capital discipline</em></p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="flip-card-container">
        <div class="flip-card">
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <div style='font-size: 3rem; margin-bottom: 1rem;'>⚖️</div>
                    <h3>Risk Assessment</h3>
                    <p>Valuation Framework</p>
                </div>
                <div class="flip-card-back">
                    <h4>Risk Factors:</h4>
                    <p><strong>Beta:</strong> Market volatility<br>
                    <strong>WACC:</strong> Cost of capital<br>
                    <strong>Terminal Value:</strong> Long-term assumptions<br>
                    <strong>Sensitivity:</strong> Key variable impact</p>
                    <p><em>Comprehensive risk-adjusted valuation</em></p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# Enhanced Sidebar Configuration
with st.sidebar:
    st.markdown("### 🏢 Company Profile")
    
    company_name = st.text_input("Company Name", value="Example Corp", 
                                help="Enter the target company name")
    
    ticker_symbol = st.text_input("Ticker Symbol", value="EXMP", 
                                 help="Stock ticker symbol")
    
    country = st.selectbox(
        "Domicile Country", 
        options=["India", "USA", "UK", "Germany", "France", "Other"],
        help="Primary country of operations"
    )
    
    industry = st.selectbox(
        "Industry Classification",
        options=list(INDUSTRY_BENCHMARKS.keys()),
        help="GICS sector classification"
    )
    
    use_industry_defaults = st.checkbox(
        "Apply Industry Benchmarks", 
        value=True,
        help="Use sector-specific financial ratios"
    )
    
    st.markdown("---")
    st.markdown("### 💹 WACC Calculation")
    
    # Enhanced risk-free rate section
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("🔄 Fetch Live Risk-Free Rate", type="primary"):
            with st.spinner(f"Fetching 10Y bond yield for {country}..."):
                scraped_rate = get_risk_free_rate(country)
                st.session_state.risk_free_rate = scraped_rate
                st.success(f"✅ Updated: {scraped_rate:.2f}%")
    
    # Initialize session state
    if 'risk_free_rate' not in st.session_state:
        st.session_state.risk_free_rate = get_risk_free_rate(country)
    
    risk_free_rate = st.number_input(
        "Risk-Free Rate (%)", 
        min_value=0.0, 
        max_value=20.0, 
        value=float(st.session_state.risk_free_rate), 
        step=0.01,
        help=f"10-year government bond yield for {country}"
    ) / 100
    
    # Enhanced beta with industry context
    industry_data = INDUSTRY_BENCHMARKS[industry]
    default_beta = industry_data["beta"] if use_industry_defaults else 1.2
    
    beta = st.number_input(
        f"Beta (Industry Avg: {industry_data['beta']:.2f})", 
        min_value=0.0, 
        max_value=3.0, 
        value=float(default_beta), 
        step=0.01,
        help="Systematic risk relative to market portfolio"
    )
    
    market_risk_premium = st.number_input(
        "Equity Risk Premium (%)", 
        min_value=0.0, 
        max_value=15.0, 
        value=6.0, 
        step=0.1,
        help="Expected market return above risk-free rate"
    ) / 100
    
    cost_of_debt = st.number_input(
        "Pre-tax Cost of Debt (%)", 
        min_value=0.0, 
        max_value=25.0, 
        value=8.0, 
        step=0.1,
        help="Weighted average interest rate on debt"
    ) / 100
    
    tax_rate = st.number_input(
        "Marginal Tax Rate (%)", 
        min_value=0.0, 
        max_value=50.0, 
        value=25.0, 
        step=0.5,
        help="Effective corporate tax rate"
    ) / 100
    
    equity_ratio = st.slider(
        "Target Equity Weight (%)", 
        min_value=10, 
        max_value=100, 
        value=70,
        help="Market value weight of equity in capital structure"
    )

# Calculate enhanced metrics
debt_ratio = 100 - equity_ratio
currency_symbol = {"India": "₹", "USA": "$", "UK": "£", "Germany": "€", "France": "€"}.get(country, "₹")

cost_of_equity = risk_free_rate + beta * market_risk_premium
wacc = (equity_ratio / 100) * cost_of_equity + (debt_ratio / 100) * cost_of_debt * (1 - tax_rate)

# Enhanced WACC display
st.markdown("### 📊 Cost of Capital Analysis")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h4 style='margin: 0 0 0.5rem 0; color: #374151;'>Risk-Free Rate</h4>
        <h2 style='margin: 0; color: #1f2937;'>{risk_free_rate * 100:.2f}%</h2>
        <p style='margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.875rem;'>10Y Government Bond</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <h4 style='margin: 0 0 0.5rem 0; color: #374151;'>Cost of Equity</h4>
        <h2 style='margin: 0; color: #1f2937;'>{cost_of_equity * 100:.2f}%</h2>
        <p style='margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.875rem;'>CAPM Model</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <h4 style='margin: 0 0 0.5rem 0; color: #374151;'>After-tax Cost of Debt</h4>
        <h2 style='margin: 0; color: #1f2937;'>{cost_of_debt * (1-tax_rate) * 100:.2f}%</h2>
        <p style='margin: 0.5rem 0 0 0; color: #6b7280; font-size: 0.875rem;'>Tax-Adjusted</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="valuation-highlight">
        <h4 style='margin: 0 0 0.5rem 0; color: white;'>WACC</h4>
        <h1 style='margin: 0; color: white; font-size: 2rem;'>{wacc * 100:.2f}%</h1>
        <p style='margin: 0.5rem 0 0 0; color: rgba(255,255,255,0.8); font-size: 0.875rem;'>Discount Rate</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# Main Financial Inputs
st.markdown("### 📈 Financial Projections & Analysis")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Core Financials", "💰 Cash Flow", "🎯 Valuation", "📋 Report"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Historical & Projected Financial Data")
        
        # Get industry defaults
        industry_data = INDUSTRY_BENCHMARKS[industry] if use_industry_defaults else {}
        
        current_revenue = st.number_input(
            f"Current Revenue ({currency_symbol} Millions)", 
            min_value=0.1, 
            value=1000.0, 
            step=10.0,
            help="Latest twelve months (LTM) revenue"
        )
        
        col_growth, col_margin = st.columns(2)
        with col_growth:
            revenue_growth_1 = st.number_input(
                "Year 1 Revenue Growth (%)", 
                min_value=-50.0, 
                max_value=100.0, 
                value=industry_data.get("typical_growth_high", 15.0), 
                step=0.1
            ) / 100
            
            revenue_growth_2 = st.number_input(
                "Year 2 Revenue Growth (%)", 
                min_value=-50.0, 
                max_value=100.0, 
                value=industry_data.get("typical_growth_high", 15.0) * 0.8, 
                step=0.1
            ) / 100
            
            revenue_growth_3 = st.number_input(
                "Year 3 Revenue Growth (%)", 
                min_value=-50.0, 
                max_value=100.0, 
                value=industry_data.get("typical_growth_high", 15.0) * 0.6, 
                step=0.1
            ) / 100
            
            revenue_growth_4 = st.number_input(
                "Year 4 Revenue Growth (%)", 
                min_value=-50.0, 
                max_value=100.0, 
                value=industry_data.get("typical_growth_mature", 8.0), 
                step=0.1
            ) / 100
            
            revenue_growth_5 = st.number_input(
                "Year 5 Revenue Growth (%)", 
                min_value=-50.0, 
                max_value=100.0, 
                value=industry_data.get("typical_growth_mature", 5.0), 
                step=0.1
            ) / 100
            
        with col_margin:
            ebitda_margin_1 = st.number_input(
                "Year 1 EBITDA Margin (%)", 
                min_value=-20.0, 
                max_value=60.0, 
                value=industry_data.get("ebitda_margin", 20.0), 
                step=0.1
            ) / 100
            
            ebitda_margin_2 = st.number_input(
                "Year 2 EBITDA Margin (%)", 
                min_value=-20.0, 
                max_value=60.0, 
                value=industry_data.get("ebitda_margin", 20.0) * 1.05, 
                step=0.1
            ) / 100
            
            ebitda_margin_3 = st.number_input(
                "Year 3 EBITDA Margin (%)", 
                min_value=-20.0, 
                max_value=60.0, 
                value=industry_data.get("ebitda_margin", 20.0) * 1.1, 
                step=0.1
            ) / 100
            
            ebitda_margin_4 = st.number_input(
                "Year 4 EBITDA Margin (%)", 
                min_value=-20.0, 
                max_value=60.0, 
                value=industry_data.get("ebitda_margin", 20.0) * 1.15, 
                step=0.1
            ) / 100
            
            ebitda_margin_5 = st.number_input(
                "Year 5 EBITDA Margin (%)", 
                min_value=-20.0, 
                max_value=60.0, 
                value=industry_data.get("ebitda_margin", 20.0) * 1.2, 
                step=0.1
            ) / 100

    with col2:
        st.markdown("#### Key Assumptions")
        
        # Capital expenditure and depreciation
        capex_revenue_ratio = st.number_input(
            "CapEx as % of Revenue", 
            min_value=0.0, 
            max_value=30.0, 
            value=industry_data.get("capex_rev", 8.0), 
            step=0.1,
            help="Capital expenditures as percentage of revenue"
        ) / 100
        
        depreciation_revenue_ratio = st.number_input(
            "Depreciation as % of Revenue", 
            min_value=0.0, 
            max_value=20.0, 
            value=industry_data.get("depreciation_rev", 6.0), 
            step=0.1,
            help="Depreciation expense as percentage of revenue"
        ) / 100
        
        working_capital_change_ratio = st.number_input(
            "Working Capital Change as % of Revenue", 
            min_value=-10.0, 
            max_value=15.0, 
            value=industry_data.get("wc_change_rev", 3.0), 
            step=0.1,
            help="Annual change in working capital as % of revenue growth"
        ) / 100
        
        terminal_growth_rate = st.number_input(
            "Terminal Growth Rate (%)", 
            min_value=0.0, 
            max_value=5.0, 
            value=2.5, 
            step=0.1,
            help="Long-term perpetual growth rate (typically GDP growth)"
        ) / 100

with tab2:
    # Calculate projected financials
    revenue_projections = []
    ebitda_projections = []
    fcf_projections = []
    years = ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"]
    
    revenue_growth_rates = [revenue_growth_1, revenue_growth_2, revenue_growth_3, revenue_growth_4, revenue_growth_5]
    ebitda_margins = [ebitda_margin_1, ebitda_margin_2, ebitda_margin_3, ebitda_margin_4, ebitda_margin_5]
    
    # Build financial projections
    for i, (growth_rate, margin) in enumerate(zip(revenue_growth_rates, ebitda_margins)):
        if i == 0:
            revenue = current_revenue * (1 + growth_rate)
        else:
            revenue = revenue_projections[i-1] * (1 + growth_rate)
        
        ebitda = revenue * margin
        depreciation = revenue * depreciation_revenue_ratio
        ebit = ebitda - depreciation
        taxes = ebit * tax_rate if ebit > 0 else 0
        nopat = ebit - taxes
        
        capex = revenue * capex_revenue_ratio
        wc_change = revenue * growth_rate * working_capital_change_ratio if i > 0 else 0
        
        fcf = nopat + depreciation - capex - wc_change
        
        revenue_projections.append(revenue)
        ebitda_projections.append(ebitda)
        fcf_projections.append(fcf)
    
    # Display financial projections table
    st.markdown("#### 📊 5-Year Financial Projections")
    
    projections_df = pd.DataFrame({
        'Year': years,
        f'Revenue ({currency_symbol}M)': [f"{rev:.1f}" for rev in revenue_projections],
        f'EBITDA ({currency_symbol}M)': [f"{ebitda:.1f}" for ebitda in ebitda_projections],
        'EBITDA Margin (%)': [f"{margin*100:.1f}%" for margin in ebitda_margins],
        f'Free Cash Flow ({currency_symbol}M)': [f"{fcf:.1f}" for fcf in fcf_projections],
        'Revenue Growth (%)': [f"{growth*100:.1f}%" for growth in revenue_growth_rates]
    })
    
    st.dataframe(projections_df, use_container_width=True)
    
    # Cash flow visualization
    fig_cf = go.Figure()
    
    fig_cf.add_trace(go.Scatter(
        x=years, 
        y=revenue_projections,
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8)
    ))
    
    fig_cf.add_trace(go.Scatter(
        x=years, 
        y=ebitda_projections,
        mode='lines+markers',
        name='EBITDA',
        line=dict(color='#764ba2', width=3),
        marker=dict(size=8)
    ))
    
    fig_cf.add_trace(go.Bar(
        x=years,
        y=fcf_projections,
        name='Free Cash Flow',
        marker_color='rgba(255, 107, 107, 0.7)',
        yaxis='y'
    ))
    
    fig_cf.update_layout(
        title="Financial Projections Overview",
        xaxis_title="Projection Period",
        yaxis_title=f"Amount ({currency_symbol} Millions)",
        template="plotly_white",
        height=500,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_cf, use_container_width=True)

with tab3:
    st.markdown("#### 🎯 DCF Valuation Analysis")
    
    # Additional valuation inputs
    col1, col2 = st.columns(2)
    
    with col1:
        shares_outstanding = st.number_input(
            "Shares Outstanding (Millions)", 
            min_value=0.1, 
            value=10.0, 
            step=1.0,
            help="Current number of shares outstanding"
        )
        
        net_debt = st.number_input(
            f"Net Debt ({currency_symbol} Millions)", 
            value=10.0, 
            step=10.0,
            help="Total debt minus cash and equivalents"
        )
    
    with col2:
        # Monte Carlo simulation parameters
        st.markdown("##### Monte Carlo Analysis")
        run_monte_carlo = st.checkbox("Enable Monte Carlo Simulation", value=True)
        num_simulations = st.slider("Number of Simulations", 1000, 10000, 5000, step=1000) if run_monte_carlo else 1000
    
    # DCF Calculation
    discount_factors = [(1 + wacc) ** i for i in range(1, 6)]
    pv_fcf = [fcf / df for fcf, df in zip(fcf_projections, discount_factors)]
    
    # Terminal value calculation
    terminal_fcf = fcf_projections[-1] * (1 + terminal_growth_rate)
    terminal_value = terminal_fcf / (wacc - terminal_growth_rate)
    pv_terminal_value = terminal_value / discount_factors[-1]
    
    # Enterprise and equity value
    enterprise_value = sum(pv_fcf) + pv_terminal_value
    equity_value = enterprise_value - net_debt
    value_per_share = equity_value / shares_outstanding
    
    # Monte Carlo simulation (if enabled)
    if run_monte_carlo:
        st.markdown("##### 🎲 Monte Carlo Simulation Results")
        
        # Generate random variations for key inputs
        np.random.seed(42)  # For reproducibility
        
        # Create distributions for key variables
        wacc_dist = np.random.normal(wacc, wacc * 0.15, num_simulations)  # 15% std dev
        terminal_growth_dist = np.random.normal(terminal_growth_rate, terminal_growth_rate * 0.3, num_simulations)
        
        # Revenue growth distributions
        rev_growth_dist = []
        for growth in revenue_growth_rates:
            rev_growth_dist.append(np.random.normal(growth, abs(growth) * 0.25, num_simulations))
        
        # EBITDA margin distributions
        ebitda_margin_dist = []
        for margin in ebitda_margins:
            ebitda_margin_dist.append(np.random.normal(margin, margin * 0.15, num_simulations))
        
        # Run simulations
        simulation_results = []
        
        for i in range(num_simulations):
            # Get random values for this simulation
            sim_wacc = max(0.05, min(0.25, wacc_dist[i]))  # Constrain WACC between 5-25%
            sim_terminal_growth = max(0.0, min(0.05, terminal_growth_dist[i]))  # Constrain terminal growth 0-5%
            
            # Calculate FCF projections for this simulation
            sim_fcf = []
            sim_revenue = current_revenue
            
            for j in range(5):
                sim_rev_growth = max(-0.5, min(1.0, rev_growth_dist[j][i]))  # Constrain growth -50% to 100%
                sim_ebitda_margin = max(0.0, min(0.6, ebitda_margin_dist[j][i]))  # Constrain margin 0-60%
                
                sim_revenue = sim_revenue * (1 + sim_rev_growth)
                sim_ebitda = sim_revenue * sim_ebitda_margin
                sim_depreciation = sim_revenue * depreciation_revenue_ratio
                sim_ebit = sim_ebitda - sim_depreciation
                sim_taxes = sim_ebit * tax_rate if sim_ebit > 0 else 0
                sim_nopat = sim_ebit - sim_taxes
                
                sim_capex = sim_revenue * capex_revenue_ratio
                sim_wc_change = sim_revenue * sim_rev_growth * working_capital_change_ratio if j > 0 else 0
                
                sim_fcf_year = sim_nopat + sim_depreciation - sim_capex - sim_wc_change
                sim_fcf.append(sim_fcf_year)
            
            # Calculate enterprise value for this simulation
            sim_discount_factors = [(1 + sim_wacc) ** k for k in range(1, 6)]
            sim_pv_fcf = [fcf / df for fcf, df in zip(sim_fcf, sim_discount_factors)]
            
            if sim_wacc > sim_terminal_growth:  # Ensure valid terminal value calculation
                sim_terminal_fcf = sim_fcf[-1] * (1 + sim_terminal_growth)
                sim_terminal_value = sim_terminal_fcf / (sim_wacc - sim_terminal_growth)
                sim_pv_terminal_value = sim_terminal_value / sim_discount_factors[-1]
                
                sim_enterprise_value = sum(sim_pv_fcf) + sim_pv_terminal_value
                sim_equity_value = sim_enterprise_value - net_debt
                sim_value_per_share = sim_equity_value / shares_outstanding
                
                simulation_results.append(sim_value_per_share)
        
        # Filter out extreme outliers (beyond 3 standard deviations)
        if simulation_results:
            sim_mean = np.mean(simulation_results)
            sim_std = np.std(simulation_results)
            simulation_results = [x for x in simulation_results if abs(x - sim_mean) <= 3 * sim_std]
        
        # Calculate statistics
        if simulation_results:
            percentiles = np.percentile(simulation_results, [10, 25, 50, 75, 90])
            
            # Display results
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style='color: #dc2626;'>🐻 Bear Case (10th %ile)</h4>
                    <h2 style='color: #dc2626;'>{format_currency(percentiles[0], currency_symbol)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="valuation-highlight">
                    <h4>🎯 Base Case (Median)</h4>
                    <h1 style='font-size: 2rem; margin: 0;'>{format_currency(percentiles[2], currency_symbol)}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <h4 style='color: #16a34a;'>🐂 Bull Case (90th %ile)</h4>
                    <h2 style='color: #16a34a;'>{format_currency(percentiles[4], currency_symbol)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            # Valuation distribution chart
            fig_dist = go.Figure()
            
            fig_dist.add_trace(go.Histogram(
                x=simulation_results,
                nbinsx=50,
                name='Valuation Distribution',
                marker_color='rgba(102, 126, 234, 0.7)',
                opacity=0.7
            ))
            
            # Add percentile lines
            colors = ['#dc2626', '#ea580c', '#16a34a', '#ca8a04', '#16a34a']
            labels = ['10th %ile (Bear)', '25th %ile', '50th %ile (Base)', '75th %ile', '90th %ile (Bull)']
            
            for i, (perc, color, label) in enumerate(zip(percentiles, colors, labels)):
                fig_dist.add_vline(x=perc, line_dash="dash", line_color=color, 
                                 annotation_text=label, annotation_position="top")
            
            fig_dist.update_layout(
                title="Monte Carlo Valuation Distribution",
                xaxis_title=f"Value Per Share ({currency_symbol})",
                yaxis_title="Frequency",
                template="plotly_white",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Summary statistics
            st.markdown("##### 📊 Statistical Summary")
            stats_df = pd.DataFrame({
                'Metric': ['Mean', 'Standard Deviation', 'Coefficient of Variation', 'Probability of Positive Value'],
                'Value': [
                    format_currency(np.mean(simulation_results), currency_symbol),
                    format_currency(np.std(simulation_results), currency_symbol),
                    f"{np.std(simulation_results)/np.mean(simulation_results)*100:.1f}%",
                    f"{len([x for x in simulation_results if x > 0])/len(simulation_results)*100:.1f}%"
                ]
            })
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
    
    else:
        # Simple deterministic valuation
        st.markdown(f"""
        <div class="executive-summary">
            <h3 style='margin-top: 0;'>🏛️ DCF Valuation Summary</h3>
            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 2rem;'>
                <div>
                    <h4>Present Value of FCF (Years 1-5)(In millions)</h4>
                    <h2>{format_currency(sum(pv_fcf), currency_symbol)}</h2>
                </div>
                <div>
                    <h4>Present Value of Terminal Value (In millions)</h4>
                    <h2>{format_currency(pv_terminal_value, currency_symbol)}</h2>
                </div>
                <div>
                    <h4>Enterprise Value (In millions)</h4>
                    <h2>{format_currency(enterprise_value, currency_symbol)}</h2>
                </div>
                <div>
                    <h4>Equity Value(In millions)</h4>
                    <h2>{format_currency(equity_value, currency_symbol)}</h2>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="valuation-highlight">
            <h2 style='margin: 0;'>Intrinsic Value Per Share</h2>
            <h1 style='font-size: 3rem; margin: 1rem 0;'>{format_currency(value_per_share, currency_symbol)}</h1>
            <p style='margin: 0; opacity: 0.9;'>Based on DCF Analysis</p>
        </div>
        """, unsafe_allow_html=True)

    # Sensitivity analysis
    st.markdown("##### 🌡️ Sensitivity Analysis")
    
    # WACC sensitivity range
    wacc_range = np.linspace(wacc * 0.7, wacc * 1.3, 11)
    terminal_range = np.linspace(terminal_growth_rate * 0.5, min(terminal_growth_rate * 2, 0.05), 11)
    
    # Create sensitivity matrix
    sensitivity_matrix = []
    for w in wacc_range:
        row = []
        for tg in terminal_range:
            if w > tg:  # Ensure valid calculation
                sens_terminal_fcf = fcf_projections[-1] * (1 + tg)
                sens_terminal_value = sens_terminal_fcf / (w - tg)
                sens_pv_terminal_value = sens_terminal_value / ((1 + w) ** 5)
                sens_enterprise_value = sum([fcf / ((1 + w) ** i) for i, fcf in enumerate(fcf_projections, 1)]) + sens_pv_terminal_value
                sens_equity_value = sens_enterprise_value - net_debt
                sens_value_per_share = sens_equity_value / shares_outstanding
                row.append(sens_value_per_share)
            else:
                row.append(np.nan)
        sensitivity_matrix.append(row)
    
    # Create sensitivity heatmap
    fig_sens = go.Figure(data=go.Heatmap(
        z=sensitivity_matrix,
        x=[f"{tg*100:.1f}%" for tg in terminal_range],
        y=[f"{w*100:.1f}%" for w in wacc_range],
        colorscale='RdYlGn',
        text=[[format_currency(val, currency_symbol) if not np.isnan(val) else 'N/A' for val in row] for row in sensitivity_matrix],
        texttemplate="%{text}",
        textfont={"size": 10},
        showscale=True,
        colorbar=dict(title=f"Value Per Share ({currency_symbol})")
    ))
    
    fig_sens.update_layout(
        title="Sensitivity Analysis: WACC vs Terminal Growth Rate",
        xaxis_title="Terminal Growth Rate",
        yaxis_title="WACC",
        height=500
    )
    
    st.plotly_chart(fig_sens, use_container_width=True)

with tab4:
    st.markdown("### 📋 Executive Investment Report")
    
    # Calculate comprehensive financial ratios
    ratios = calculate_financial_ratios(
        revenue=[current_revenue] + revenue_projections,
        ebitda=[current_revenue * ebitda_margins[0]] + ebitda_projections,
        fcf=[0] + fcf_projections,  # Assuming current FCF is unknown
        capex=[current_revenue * capex_revenue_ratio] * 6,
        shares_outstanding=shares_outstanding
    )
    
    # Determine risk level
    fcf_volatility = np.std(fcf_projections) / np.mean(fcf_projections) if np.mean(fcf_projections) > 0 else 0.5
    risk_assessment, risk_color = determine_risk_level(beta, industry, debt_ratio, fcf_volatility)
    
    # Investment recommendation logic
    current_market_price = st.number_input(
        f"Current Market Price ({currency_symbol})", 
        min_value=0.1, 
        value=float(value_per_share * 0.9), 
        step=0.01,
        help="Current trading price per share"
    )
    
    # Determine recommendation
    if run_monte_carlo and simulation_results:
        base_case_value = percentiles[2]  # Median from Monte Carlo
        upside_potential = (base_case_value - current_market_price) / current_market_price
    else:
        base_case_value = value_per_share
        upside_potential = (value_per_share - current_market_price) / current_market_price
    
    if upside_potential > 0.20:
        recommendation = "🟢 STRONG BUY"
        rec_color = "#16a34a"
    elif upside_potential > 0.10:
        recommendation = "🟢 BUY" 
        rec_color = "#22c55e"
    elif upside_potential > -0.10:
        recommendation = "🟡 HOLD"
        rec_color = "#eab308"
    elif upside_potential > -0.25:
        recommendation = "🔴 SELL"
        rec_color = "#ef4444"
    else:
        recommendation = "🔴 STRONG SELL"
        rec_color = "#dc2626"
    
    # Executive Summary
    st.markdown(f"""
    <div class="executive-summary">
        <h2 style='margin-top: 0;'>🏛️ Executive Summary - {company_name}</h2>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin: 2rem 0;'>
            <div>
                <h4>Investment Thesis</h4>
                <p>{company_name} operates in the {industry.lower()} sector with {"strong" if upside_potential > 0.1 else "moderate" if upside_potential > -0.1 else "weak"} financial fundamentals and {"attractive" if upside_potential > 0 else "limited"} growth prospects.</p>
            </div>
            <div>
                <h4>Key Financial Metrics</h4>
                <p>• Revenue CAGR: {ratios.get('revenue_cagr', 0)*100:.1f}%<br>
                • Avg EBITDA Margin: {ratios.get('avg_ebitda_margin', 0)*100:.1f}%<br>
                • FCF Margin: {ratios.get('avg_fcf_margin', 0)*100:.1f}%</p>
            </div>
            <div>
                <h4>Valuation Metrics</h4>
                <p>• Intrinsic Value: {format_currency(base_case_value, currency_symbol)}<br>
                • Current Price: {format_currency(current_market_price, currency_symbol)}<br>
                • Upside Potential: {upside_potential*100:.1f}%</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Investment recommendation
    st.markdown(f"""
    <div class="recommendation-box" style='background: linear-gradient(135deg, {rec_color}, {rec_color}88);'>
        <h2 style='margin: 0; font-size: 2.5rem;'>{recommendation}</h2>
        <h3 style='margin: 1rem 0;'>Target Price: {format_currency(base_case_value, currency_symbol)}</h3>
        <p style='margin: 0; font-size: 1.1rem;'>Upside Potential: {upside_potential*100:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Risk assessment
    st.markdown(f"""
    <div class="risk-analysis">
        <h3 style='margin-top: 0;'>⚠️ Risk Assessment: {risk_assessment}</h3>
        <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 1rem;'>
            <div>
                <strong>Market Risk (Beta):</strong> {beta:.2f}<br>
                <small>{"High" if beta > 1.2 else "Moderate" if beta > 0.8 else "Low"} market sensitivity</small>
            </div>
            <div>
                <strong>Financial Risk:</strong> {debt_ratio:.0f}% Debt<br>
                <small>{"High" if debt_ratio > 50 else "Moderate" if debt_ratio > 30 else "Low"} leverage</small>
            </div>
            <div>
                <strong>Industry Risk:</strong> {industry}<br>
                <small>{"Cyclical" if industry in ["Technology", "Energy"] else "Defensive"} sector characteristics</small>
            </div>
            <div>
                <strong>Cash Flow Volatility:</strong> {fcf_volatility*100:.1f}%<br>
                <small>{"High" if fcf_volatility > 0.3 else "Moderate" if fcf_volatility > 0.15 else "Low"} variability</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
   # Generate and display investment thesis
    valuation_results = {
        'bear': format_currency(percentiles[0], currency_symbol) if run_monte_carlo and simulation_results else format_currency(value_per_share * 0.8, currency_symbol),
        'base': format_currency(percentiles[2], currency_symbol) if run_monte_carlo and simulation_results else format_currency(value_per_share, currency_symbol),
        'bull': format_currency(percentiles[4], currency_symbol) if run_monte_carlo and simulation_results else format_currency(value_per_share * 1.2, currency_symbol),
        'weighted_avg': format_currency(np.mean(simulation_results), currency_symbol) if run_monte_carlo and simulation_results else format_currency(value_per_share, currency_symbol)
    }
    
    # Generate comprehensive investment thesis
    investment_thesis = generate_investment_thesis(
        company_name, industry, ratios, valuation_results, recommendation
    )
    
    # Display investment thesis in expandable section
    with st.expander("📄 Detailed Investment Thesis & Valuation Report", expanded=False):
        st.markdown(investment_thesis)
    
    # Key metrics comparison table
    st.markdown("##### 📊 Peer Comparison & Industry Benchmarks")
    
    industry_data = INDUSTRY_BENCHMARKS[industry]
    comparison_df = pd.DataFrame({
        'Metric': [
            'EBITDA Margin (%)',
            'CapEx/Revenue (%)', 
            'Beta',
            'Debt/Equity Ratio',
            'ROE (%)',
            'ROIC (%)',
            'Revenue Multiple (x)'
        ],
        f'{company_name} (Projected)': [
            f"{ratios.get('avg_ebitda_margin', 0)*100:.1f}%",
            f"{capex_revenue_ratio*100:.1f}%",
            f"{beta:.2f}",
            f"{debt_ratio/equity_ratio:.2f}",
            "N/A",  # Would need additional inputs
            "N/A",  # Would need additional inputs
            f"{base_case_value/(revenue_projections[-1]/shares_outstanding):.1f}x"
        ],
        f'{industry} Industry Average': [
            f"{industry_data['ebitda_margin']:.1f}%",
            f"{industry_data['capex_rev']:.1f}%",
            f"{industry_data['beta']:.2f}",
            f"{industry_data['debt_equity']:.2f}",
            f"{industry_data['roe']:.1f}%",
            f"{industry_data['roic']:.1f}%",
            f"{industry_data['revenue_multiple']:.1f}x"
        ],
        'Relative Position': [
            "🟢 Above" if ratios.get('avg_ebitda_margin', 0)*100 > industry_data['ebitda_margin'] else "🔴 Below",
            "🟡 Higher" if capex_revenue_ratio*100 > industry_data['capex_rev'] else "🟢 Lower",
            "🔴 Higher Risk" if beta > industry_data['beta'] else "🟢 Lower Risk",
            "🔴 Higher" if debt_ratio/equity_ratio > industry_data['debt_equity'] else "🟢 Lower",
            "🟡 N/A",
            "🟡 N/A", 
            "🟢 Premium" if base_case_value/(revenue_projections[-1]/shares_outstanding) > industry_data['revenue_multiple'] else "🔴 Discount"
        ]
    })
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # Valuation bridge chart
    st.markdown("##### 🌉 Valuation Bridge Analysis")
    
    bridge_categories = [
        'Current Market Price',
        'DCF Base Case', 
        'Monte Carlo Adjustment',
        'Risk Premium',
        'Final Target Price'
    ]
    
    monte_carlo_adj = (percentiles[2] - value_per_share) if run_monte_carlo and simulation_results else 0
    risk_premium = base_case_value * 0.05 if upside_potential > 0.15 else -base_case_value * 0.05
    
    bridge_values = [
        current_market_price,
        value_per_share - current_market_price,
        monte_carlo_adj,
        risk_premium,
        base_case_value - current_market_price - (value_per_share - current_market_price) - monte_carlo_adj - risk_premium
    ]
    
    bridge_cumulative = [current_market_price]
    for i in range(1, len(bridge_values)):
        bridge_cumulative.append(bridge_cumulative[-1] + bridge_values[i])
    
    fig_bridge = go.Figure()
    
    # Starting point
    fig_bridge.add_trace(go.Bar(
        x=[bridge_categories[0]], 
        y=[bridge_values[0]],
        name='Current Price',
        marker_color='lightblue',
        text=[format_currency(bridge_values[0], currency_symbol)],
        textposition='auto'
    ))
    
    # Adjustments
    colors = ['green' if val > 0 else 'red' for val in bridge_values[1:-1]]
    for i in range(1, len(bridge_values)-1):
        fig_bridge.add_trace(go.Bar(
            x=[bridge_categories[i]], 
            y=[bridge_values[i]],
            name=bridge_categories[i],
            marker_color=colors[i-1],
            text=[f"+{format_currency(bridge_values[i], currency_symbol)}" if bridge_values[i] > 0 else format_currency(bridge_values[i], currency_symbol)],
            textposition='auto'
        ))
    
    # Final target
    fig_bridge.add_trace(go.Bar(
        x=[bridge_categories[-1]], 
        y=[base_case_value],
        name='Target Price',
        marker_color='darkgreen',
        text=[format_currency(base_case_value, currency_symbol)],
        textposition='auto'
    ))
    
    fig_bridge.update_layout(
        title="Valuation Bridge: From Current Price to Target Price",
        xaxis_title="Valuation Components",
        yaxis_title=f"Price Per Share ({currency_symbol})",
        template="plotly_white",
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig_bridge, use_container_width=True)
    
# Footer with disclaimer
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

st.markdown("""
<div style='background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 2rem; border-radius: 15px; margin: 2rem 0; text-align: center; border: 1px solid #e2e8f0;'>
    <h4 style='color: #374151; margin-bottom: 1rem;'>⚖️ Important Disclaimer</h4>
    <p style='color: #6b7280; margin: 0; line-height: 1.6;'>
        <strong>This DCF valuation model is designed for educational and analytical purposes only.</strong><br>
        The projections, assumptions, and valuations presented here should not be considered as investment advice or recommendations. 
        All financial models involve inherent uncertainties and risks. Past performance does not guarantee future results.<br>
        <em>Please consult with qualified financial professionals before making investment decisions.</em>
    </p>
    <div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #d1d5db;'>
        <small style='color: #9ca3af;'>
            © 2025 Investment Banking DCF Model | Built with Streamlit | 
            <a href="#" style='color: #4f46e5;'>Documentation</a> | 
            <a href="#" style='color: #4f46e5;'>Support</a>
        </small>
    </div>
</div>
""", unsafe_allow_html=True)

# Interactive 3D DCF Visualization
with st.expander("🎯 Interactive 3D DCF Model Visualization", expanded=True):
    st.markdown("### 🌐 Interactive 3D Valuation Explorer")
    
    # Create interactive 3D surface plot for DCF sensitivity
    wacc_3d_range = np.linspace(wacc * 0.7, wacc * 1.3, 20)
    terminal_3d_range = np.linspace(max(terminal_growth_rate * 0.5, 0.005), min(terminal_growth_rate * 2, 0.05), 20)
    revenue_growth_3d_range = np.linspace(max(revenue_growth_rates[0] * 0.5, -0.1), revenue_growth_rates[0] * 1.5, 20)
    
    # Create 3D mesh
    wacc_mesh, terminal_mesh, growth_mesh = np.meshgrid(wacc_3d_range, terminal_3d_range, revenue_growth_3d_range)
    
    # Calculate valuation surface
    valuation_surface = np.zeros_like(wacc_mesh)
    
    for i in range(wacc_mesh.shape[0]):
        for j in range(wacc_mesh.shape[1]):
            for k in range(wacc_mesh.shape[2]):
                w = wacc_mesh[i,j,k]
                tg = terminal_mesh[i,j,k] 
                rg = growth_mesh[i,j,k]
                
                if w > tg:  # Valid calculation
                    try:
                        # Adjust FCF based on revenue growth
                        adj_fcf = [fcf * (1 + (rg - revenue_growth_rates[idx]) * 0.5) for idx, fcf in enumerate(fcf_projections)]
                        adj_terminal_fcf = adj_fcf[-1] * (1 + tg)
                        
                        # Calculate enterprise value
                        pv_fcf_3d = sum([fcf / ((1 + w) ** idx) for idx, fcf in enumerate(adj_fcf, 1)])
                        terminal_val_3d = adj_terminal_fcf / (w - tg)
                        pv_terminal_3d = terminal_val_3d / ((1 + w) ** 5)
                        
                        enterprise_val_3d = pv_fcf_3d + pv_terminal_3d
                        equity_val_3d = enterprise_val_3d - net_debt
                        valuation_surface[i,j,k] = max(0, equity_val_3d / shares_outstanding)
                    except:
                        valuation_surface[i,j,k] = 0
                else:
                    valuation_surface[i,j,k] = 0
    
    # Create 3D scatter plot for Monte Carlo results
    if run_monte_carlo and simulation_results and len(simulation_results) > 100:
        try:
            # Sample points for visualization with better distribution
            sample_size = min(500, len(simulation_results))  # Reduced for less clustering
            sample_indices = np.random.choice(len(simulation_results), sample_size, replace=False)
            sample_values = [simulation_results[i] for i in sample_indices]
            
            # Create more spread out variations for better visualization
            wacc_min, wacc_max = wacc * 0.7, wacc * 1.3
            terminal_min, terminal_max = max(terminal_growth_rate * 0.3, 0.005), min(terminal_growth_rate * 2.5, 0.05)
            
            # Use uniform distribution for better spread
            wacc_scatter = np.random.uniform(wacc_min, wacc_max, sample_size)
            terminal_scatter = np.random.uniform(terminal_min, terminal_max, sample_size)
            
            # Filter out invalid combinations (WACC <= Terminal Growth)
            valid_indices = wacc_scatter > terminal_scatter
            wacc_scatter = wacc_scatter[valid_indices]
            terminal_scatter = terminal_scatter[valid_indices]
            sample_values = [sample_values[i] for i, valid in enumerate(valid_indices) if valid]
            
            # Ensure we have valid data
            if len(sample_values) > 0 and len(wacc_scatter) > 0:
                # Create size variation based on probability density
                marker_sizes = []
                for v in sample_values:
                    if abs(v - np.median(simulation_results)) < np.std(simulation_results) * 0.5:
                        marker_sizes.append(8)  # Larger for values near median
                    elif abs(v - np.median(simulation_results)) < np.std(simulation_results):
                        marker_sizes.append(6)  # Medium size
                    else:
                        marker_sizes.append(4)  # Smaller for outliers
                
                # Ensure all arrays have the same length
                min_length = min(len(wacc_scatter), len(terminal_scatter), len(sample_values), len(marker_sizes))
                wacc_scatter = wacc_scatter[:min_length]
                terminal_scatter = terminal_scatter[:min_length]
                sample_values = sample_values[:min_length]
                marker_sizes = marker_sizes[:min_length]
                
                fig_3d_scatter = go.Figure(data=[go.Scatter3d(
                    x=wacc_scatter * 100,
                    y=terminal_scatter * 100,
                    z=sample_values,
                    mode='markers',
                    marker=dict(
                        size=marker_sizes,
                        color=sample_values,
                        colorscale='Viridis',
                        opacity=0.7,
                        showscale=True
                    ),
                    text=[f'WACC: {w*100:.2f}%<br>Terminal Growth: {tg*100:.2f}%<br>Value: {format_currency(v, currency_symbol)}' 
                          for w, tg, v in zip(wacc_scatter, terminal_scatter, sample_values)],
                    name='Monte Carlo Results'
                )])
                
                # Add current market price reference plane (simplified)
                wacc_range_viz = np.linspace(wacc_min * 100, wacc_max * 100, 10)
                terminal_range_viz = np.linspace(terminal_min * 100, terminal_max * 100, 10)
                wacc_plane, terminal_plane = np.meshgrid(wacc_range_viz, terminal_range_viz)
                price_plane = np.full_like(wacc_plane, current_market_price)
                
                fig_3d_scatter.add_trace(go.Surface(
                    x=wacc_plane,
                    y=terminal_plane,
                    z=price_plane,
                    colorscale='Blues',
                    showscale=False,
                    opacity=0.3,
                    name='Current Market Price'
                ))
                
                # Add base case point
                fig_3d_scatter.add_trace(go.Scatter3d(
                    x=[wacc * 100],
                    y=[terminal_growth_rate * 100],
                    z=[value_per_share],
                    mode='markers',
                    marker=dict(
                        size=15,
                        color='red',
                        symbol='diamond'
                    ),
                    name='Base Case DCF',
                    text=[f'Base Case DCF<br>WACC: {wacc*100:.2f}%<br>Terminal Growth: {terminal_growth_rate*100:.2f}%<br>Value: {format_currency(value_per_share, currency_symbol)}']
                ))
                
                fig_3d_scatter.update_layout(
                    title="3D Monte Carlo Valuation Distribution",
                    scene=dict(
                        xaxis=dict(
                            title='WACC (%)',
                            range=[wacc_min * 100, wacc_max * 100],
                            showgrid=True
                        ),
                        yaxis=dict(
                            title='Terminal Growth Rate (%)',
                            range=[terminal_min * 100, terminal_max * 100],
                            showgrid=True
                        ),
                        zaxis=dict(
                            title=f'Value per Share ({currency_symbol})',
                            showgrid=True
                        ),
                        camera=dict(
                            up=dict(x=0, y=0, z=1),
                            center=dict(x=0, y=0, z=0),
                            eye=dict(x=1.8, y=1.8, z=1.2)
                        )
                    ),
                    height=650,
                    showlegend=True,
                    margin=dict(l=0, r=0, t=50, b=0)
                )
                
                st.plotly_chart(fig_3d_scatter, use_container_width=True)
            else:
                st.warning("Insufficient valid data points for 3D Monte Carlo visualization.")
        except Exception as e:
            st.error(f"Error creating 3D Monte Carlo plot: {str(e)}")
    
    # Create improved 3D surface plot for sensitivity analysis
try:
    # Use better resolution and spacing for surface
    wacc_surface_range = np.linspace(wacc * 0.75, wacc * 1.25, 25)
    terminal_surface_range = np.linspace(max(terminal_growth_rate * 0.4, 0.005), min(terminal_growth_rate * 2, 0.045), 25)
    
    # Calculate surface values with better error handling
    surface_values = np.zeros((len(terminal_surface_range), len(wacc_surface_range)))
    
    for i, tg in enumerate(terminal_surface_range):
        for j, w in enumerate(wacc_surface_range):
            if w > tg and w > 0.01:  # Valid calculation with minimum WACC
                try:
                    surf_terminal_fcf = fcf_projections[-1] * (1 + tg)
                    surf_terminal_value = surf_terminal_fcf / (w - tg)
                    surf_pv_terminal = surf_terminal_value / ((1 + w) ** 5)
                    surf_pv_fcf = sum([fcf / ((1 + w) ** k) for k, fcf in enumerate(fcf_projections, 1)])
                    surf_enterprise_value = surf_pv_fcf + surf_pv_terminal
                    surf_equity_value = surf_enterprise_value - net_debt
                    surface_values[i, j] = max(0, surf_equity_value / shares_outstanding)
                except:
                    surface_values[i, j] = 0
            else:
                surface_values[i, j] = 0
    
    # Clean the surface data
    surface_values = np.nan_to_num(surface_values, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Create cleaner 3D surface
    fig_3d_surface = go.Figure()
    
    # Add main surface (ultra-simplified)
    fig_3d_surface.add_trace(go.Surface(
        z=surface_values,
        x=wacc_surface_range * 100,
        y=terminal_surface_range * 100
    ))
    
    # Add contour lines at the base (simplified)
    fig_3d_surface.add_trace(go.Contour(
        z=surface_values,
        x=wacc_surface_range * 100,
        y=terminal_surface_range * 100,
        colorscale='Plasma',
        opacity=0.3,
        showscale=False,
        name='Value Contours'
    ))
    
    # Add current valuation point with better visibility
    fig_3d_surface.add_trace(go.Scatter3d(
        x=[wacc * 100],
        y=[terminal_growth_rate * 100], 
        z=[value_per_share + 50],  # Slightly elevated for visibility
        mode='markers',
        marker=dict(
            size=12,
            color='red',
            symbol='diamond'
        ),
        name='Base Case DCF'
    ))
    
    # Add current market price level as a plane (simplified)
    market_price_surface = np.full_like(surface_values, current_market_price)
    fig_3d_surface.add_trace(go.Surface(
        z=market_price_surface,
        x=wacc_surface_range * 100,
        y=terminal_surface_range * 100,
        colorscale='Reds',
        showscale=False,
        opacity=0.3,
        name='Market Price'
    ))
    
    fig_3d_surface.update_layout(
        title="3D DCF Sensitivity Analysis",
        scene=dict(
            xaxis=dict(
                title='WACC (%)',
                showgrid=True
            ),
            yaxis=dict(
                title='Terminal Growth Rate (%)',
                showgrid=True
            ),
            zaxis=dict(
                title=f'Value per Share ({currency_symbol})',
                showgrid=True
            ),
            camera=dict(
                up=dict(x=0, y=0, z=1),
                center=dict(x=0, y=0, z=0),
                eye=dict(x=2.0, y=2.0, z=1.5)
            )
        ),
        height=700,
        showlegend=True,
        margin=dict(l=0, r=0, t=60, b=0)
    )
    
    st.plotly_chart(fig_3d_surface, use_container_width=True)

except Exception as e:
    st.error(f"Error creating 3D surface plot: {str(e)}")
    # Fallback to 2D heatmap
    try:
        fig_fallback = go.Figure(data=go.Heatmap(
            z=surface_values,
            x=wacc_surface_range * 100,
            y=terminal_surface_range * 100,
            colorscale='Plasma'
        ))
        fig_fallback.update_layout(
            title="2D DCF Sensitivity Analysis (Fallback)",
            xaxis_title="WACC (%)",
            yaxis_title="Terminal Growth Rate (%)",
            height=500
        )
        st.plotly_chart(fig_fallback, use_container_width=True)
    except:
        st.error("Unable to create any sensitivity analysis plot.")

# Interactive controls for 3D exploration
st.markdown("#### 🎮 Interactive DCF Explorer")

col1, col2, col3 = st.columns(3)

with col1:
    interactive_wacc = st.slider(
        "Adjust WACC (%)", 
        min_value=float(wacc * 0.5 * 100), 
        max_value=float(wacc * 1.5 * 100), 
        value=float(wacc * 100),
        step=0.1
    ) / 100

with col2:
    interactive_terminal = st.slider(
        "Adjust Terminal Growth (%)", 
        min_value=0.5, 
        max_value=5.0, 
        value=float(terminal_growth_rate * 100),
        step=0.1
    ) / 100

with col3:
    interactive_growth = st.slider(
        "Adjust Year 1 Growth (%)", 
        min_value=float(max(revenue_growth_rates[0] * 50, -20)), 
        max_value=float(revenue_growth_rates[0] * 200), 
        value=float(revenue_growth_rates[0] * 100),
        step=1.0
    ) / 100

# Calculate interactive valuation
if interactive_wacc > interactive_terminal:
    try:
        # Adjust FCF based on growth change
        growth_multiplier = 1 + (interactive_growth - revenue_growth_rates[0]) * 0.5
        interactive_fcf = [fcf * growth_multiplier for fcf in fcf_projections]
        interactive_terminal_fcf = interactive_fcf[-1] * (1 + interactive_terminal)
        
        # Calculate valuation
        interactive_pv_fcf = sum([fcf / ((1 + interactive_wacc) ** i) for i, fcf in enumerate(interactive_fcf, 1)])
        interactive_terminal_value = interactive_terminal_fcf / (interactive_wacc - interactive_terminal)
        interactive_pv_terminal = interactive_terminal_value / ((1 + interactive_wacc) ** 5)
        
        interactive_enterprise_value = interactive_pv_fcf + interactive_pv_terminal
        interactive_equity_value = interactive_enterprise_value - net_debt
        interactive_value_per_share = interactive_equity_value / shares_outstanding
        
        interactive_upside = (interactive_value_per_share - current_market_price) / current_market_price
        
        # Display interactive results
        st.markdown(f"""
        <div class="valuation-highlight" style='background: linear-gradient(135deg, {"#16a34a" if interactive_upside > 0 else "#dc2626"} 0%, {"#22c55e" if interactive_upside > 0 else "#ef4444"} 100%);'>
            <h3 style='margin: 0;'>Interactive Valuation Result</h3>
            <h1 style='font-size: 2.5rem; margin: 1rem 0;'>{format_currency(interactive_value_per_share, currency_symbol)}</h1>
            <p style='margin: 0; font-size: 1.2rem;'>
                {"Upside" if interactive_upside > 0 else "Downside"}: {abs(interactive_upside)*100:.1f}% 
                vs Current Price ({format_currency(current_market_price, currency_symbol)})
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show impact breakdown
        col1, col2, col3 = st.columns(3)
        
        with col1:
            wacc_impact = (interactive_wacc - wacc) * 100
            st.metric("WACC Impact", f"{wacc_impact:+.2f}%", f"vs Base: {wacc*100:.2f}%")
        
        with col2:
            growth_impact = (interactive_terminal - terminal_growth_rate) * 100
            st.metric("Terminal Growth Impact", f"{growth_impact:+.2f}%", f"vs Base: {terminal_growth_rate*100:.1f}%")
        
        with col3:
            revenue_impact = (interactive_growth - revenue_growth_rates[0]) * 100
            st.metric("Revenue Growth Impact", f"{revenue_impact:+.1f}%", f"vs Base: {revenue_growth_rates[0]*100:.1f}%")
    except Exception as e:
        st.error(f"Error in interactive valuation calculation: {str(e)}")
else:
    st.error("⚠️ Invalid parameters: WACC must be greater than Terminal Growth Rate for valuation calculation.")

# Value driver waterfall in 3D
st.markdown("#### 🌊 3D Value Driver Analysis")

try:
    # Calculate component contributions
    components = ['FCF Years 1-5', 'Terminal Value', 'Net Debt Impact', 'Share Count Impact']
    base_components = [sum(pv_fcf), pv_terminal_value, -net_debt, 0]  # Share count is already in per-share calc
    
    # Create 3D bar chart
    fig_3d_bars = go.Figure(data=[go.Bar(
        x=components,
        y=base_components,
        marker_color=['#4ade80', '#22c55e', '#ef4444', '#6b7280'],
        text=[format_currency(comp, currency_symbol) for comp in base_components],
        textposition='auto'
    )])
    
    fig_3d_bars.update_layout(
        title="DCF Value Component Breakdown",
        xaxis_title="Value Components", 
        yaxis_title=f"Contribution ({currency_symbol}M)",
        template="plotly_white",
        height=400
    )
    
    st.plotly_chart(fig_3d_bars, use_container_width=True)
except Exception as e:
    st.error(f"Error creating value driver chart: {str(e)}")
# Performance metrics and model validation
if st.checkbox("🔍 Show Model Performance Metrics", value=False):
    st.markdown("### 📊 Model Performance & Validation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Key Model Statistics")
        
        # Calculate model statistics
        if run_monte_carlo and simulation_results:
            confidence_interval_95 = np.percentile(simulation_results, [2.5, 97.5])
            model_confidence = len([x for x in simulation_results if confidence_interval_95[0] <= x <= confidence_interval_95[1]]) / len(simulation_results)
            
            performance_metrics = pd.DataFrame({
                'Metric': [
                    'Simulation Count',
                    'Mean Valuation',
                    'Median Valuation', 
                    'Standard Deviation',
                    '95% Confidence Interval',
                    'Model Confidence',
                    'Probability of Positive NPV'
                ],
                'Value': [
                    f"{len(simulation_results):,}",
                    format_currency(np.mean(simulation_results), currency_symbol),
                    format_currency(np.median(simulation_results), currency_symbol),
                    format_currency(np.std(simulation_results), currency_symbol),
                    f"{format_currency(confidence_interval_95[0], currency_symbol)} - {format_currency(confidence_interval_95[1], currency_symbol)}",
                    f"{model_confidence*100:.1f}%",
                    f"{len([x for x in simulation_results if x > 0])/len(simulation_results)*100:.1f}%"
                ]
            })
            
            st.dataframe(performance_metrics, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### ⚠️ Model Risk Assessment")
        
        risk_factors = pd.DataFrame({
            'Risk Factor': [
                'Terminal Value Sensitivity',
                'WACC Assumption Risk',
                'Growth Rate Uncertainty', 
                'Cash Flow Volatility',
                'Market Conditions',
                'Industry Cyclicality'
            ],
            'Impact Level': [
                'High - 60% of total value',
                'High - Direct discount impact',
                'Medium - Early years material',
                'Medium - Historical variance',
                'High - Beta > 1.0',
                f"{'High' if industry in ['Technology', 'Energy'] else 'Medium'}"
            ],
            'Mitigation Strategy': [
                'Scenario analysis & ranges',
                'Market-based validation',
                'Conservative assumptions',
                'Monte Carlo simulation',
                'Beta adjustment factors',
                'Industry-specific benchmarks'
            ]
        })
        
        st.dataframe(risk_factors, use_container_width=True, hide_index=True)
        
