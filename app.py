"""
Project Samarth - Intelligent Q&A System
Streamlit Frontend Application - FIXED VERSION
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_collector import DataCollector
from query_engine import QueryEngine  # Use the fixed version
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Project Samarth - Agriculture Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .source-tag {
        background-color: #E8F5E9;
        padding: 0.5rem;
        border-radius: 5px;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #F1F8E9;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'query_engine' not in st.session_state:
    st.session_state.query_engine = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""

@st.cache_resource
def load_data():
    """Load and cache data"""
    try:
        collector = DataCollector()
        return collector.get_all_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def initialize_query_engine(data, api_key):
    """Initialize query engine with LLM"""
    try:
        return QueryEngine(api_key, data)
    except Exception as e:
        st.error(f"Error initializing query engine: {e}")
        return None

def render_visualizations(data):
    """Render visualizations based on data structure"""
    
    # District-level crop data visualization
    if 'highest_district' in data:
        st.markdown("### 📍 District Analysis")
        district_data = data['highest_district']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("District", district_data.get('District', 'N/A'))
        with col2:
            st.metric("Production", f"{district_data.get('Production', 0):.0f} tonnes")
        with col3:
            st.metric("Year", district_data.get('Year', 'N/A'))
        
        # Top districts bar chart
        if 'top_districts' in data and data['top_districts']:
            top_df = pd.DataFrame(data['top_districts'])
            if not top_df.empty and 'District' in top_df.columns:
                fig = px.bar(
                    top_df, 
                    x='District', 
                    y='Production',
                    title='Top Districts by Production',
                    color='Production',
                    color_continuous_scale='Greens'
                )
                fig.update_layout(xaxis_title="District", yaxis_title="Production (tonnes)")
                st.plotly_chart(fig, use_container_width=True)
    
    # Rainfall and crops comparison with year-by-year data
    elif 'rainfall' in data and 'crops' in data:
        # Year-by-year rainfall comparison
        if 'rainfall_by_year' in data:
            st.markdown("### 📊 Year-by-Year Rainfall Comparison")
            
            rainfall_yearly = data['rainfall_by_year']
            states = list(rainfall_yearly.keys())
            
            # Create line chart for yearly comparison
            fig = go.Figure()
            
            colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0']
            for idx, state in enumerate(states):
                yearly_data = rainfall_yearly[state]
                years = list(yearly_data.keys())
                values = list(yearly_data.values())
                
                fig.add_trace(go.Scatter(
                    x=years,
                    y=values,
                    name=state,
                    mode='lines+markers',
                    line=dict(color=colors[idx % len(colors)], width=3),
                    marker=dict(size=8)
                ))
            
            fig.update_layout(
                title=f"Annual Rainfall Comparison ({data.get('year_range', 'All Years')})",
                xaxis_title="Year",
                yaxis_title="Rainfall (mm)",
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Average rainfall comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Average Rainfall")
            rf_data = data['rainfall']
            if rf_data:
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(rf_data.keys()),
                        y=list(rf_data.values()),
                        marker_color=['#4CAF50', '#2196F3', '#FF9800'],
                        text=[f"{v:.1f} mm" for v in rf_data.values()],
                        textposition='outside'
                    )
                ])
                fig.update_layout(
                    title="Average Annual Rainfall",
                    xaxis_title="State",
                    yaxis_title="Rainfall (mm)",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🌾 Top Crops Production")
            # Crop production comparison
            crop_data = data['crops']
            if crop_data:
                states = list(crop_data.keys())
                if states:
                    # Create grouped bar chart for crops
                    all_crops = set()
                    for state_crops in crop_data.values():
                        all_crops.update(state_crops.keys())
                    
                    fig = go.Figure()
                    colors = ['#66BB6A', '#42A5F5', '#FFA726']
                    
                    for idx, state in enumerate(states[:2]):  # Show first 2 states
                        state_crops = crop_data[state]
                        fig.add_trace(go.Bar(
                            name=state,
                            x=list(state_crops.keys()),
                            y=list(state_crops.values()),
                            marker_color=colors[idx]
                        ))
                    
                    fig.update_layout(
                        title=f"Crop Production Comparison",
                        xaxis_title="Crop",
                        yaxis_title="Production (tonnes)",
                        barmode='group'
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    # Trend analysis
    elif 'crop_trend' in data:
        crop_trend = pd.Series(data['crop_trend'])
        rain_trend = pd.Series(data.get('rainfall_trend', {}))
        
        fig = go.Figure()
        
        # Add production line
        fig.add_trace(go.Scatter(
            x=crop_trend.index,
            y=crop_trend.values,
            name='Production',
            line=dict(color='#4CAF50', width=3),
            mode='lines+markers'
        ))
        
        # Add rainfall line if available
        if not rain_trend.empty:
            fig.add_trace(go.Scatter(
                x=rain_trend.index,
                y=rain_trend.values,
                name='Rainfall',
                yaxis='y2',
                line=dict(color='#2196F3', width=3),
                mode='lines+markers'
            ))
            
            fig.update_layout(
                title='Production & Rainfall Trend',
                xaxis_title='Year',
                yaxis_title='Production (tonnes)',
                yaxis2=dict(
                    title='Rainfall (mm)', 
                    overlaying='y', 
                    side='right'
                ),
                hovermode='x unified'
            )
        else:
            fig.update_layout(
                title='Production Trend',
                xaxis_title='Year',
                yaxis_title='Production (tonnes)',
                hovermode='x unified'
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show correlation if available
        if 'correlation' in data:
            corr = data['correlation']
            col1, col2, col3 = st.columns(3)
            with col2:
                st.metric(
                    "Correlation Coefficient", 
                    f"{corr:.3f}",
                    help="Correlation between production and rainfall"
                )

def main():
    # Header
    st.markdown('<h1 class="main-header">🌾 Project Samarth</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Intelligent Q&A System for Agriculture & Climate Data</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            help="Get your free API key from https://aistudio.google.com/app/apikey"
        )
        
        if not api_key:
            st.warning("Please enter your Gemini API key to continue")
            st.info("📌 Get free API key: [Google AI Studio](https://aistudio.google.com/app/apikey)")
        else:
            # Load data button
            if st.button("🔄 Load Data", use_container_width=True):
                with st.spinner("Loading datasets from data.gov.in..."):
                    data = load_data()
                    if data:
                        st.session_state.data = data
                        engine = initialize_query_engine(data, api_key)
                        if engine:
                            st.session_state.query_engine = engine
                            st.session_state.data_loaded = True
                            st.success("✅ Data loaded successfully!")
                        else:
                            st.error("❌ Failed to initialize query engine")
                    else:
                        st.error("❌ Failed to load data")
        
        st.divider()
        
        # Data statistics
        if st.session_state.data_loaded:
            st.subheader("📊 Data Statistics")
            data = st.session_state.data
            
            st.metric("Crop Records", len(data['crop_production']))
            st.metric("Rainfall Records", len(data['rainfall']))
            st.metric("States", data['crop_production']['State'].nunique())
            st.metric("Crops", data['crop_production']['Crop'].nunique())
            st.metric("Years", f"{data['crop_production']['Year'].min()}-{data['crop_production']['Year'].max()}")
        
        st.divider()
        
        # Sample questions
        st.subheader("💡 Sample Questions")
        sample_questions = [
            "What is the area of  rice cultivation in Amritsar district punjab in 2020 ?",
            "Which district has highest wheat production in Punjab ?",
            "Which district has highest wheat production in Punjab in Rabi season in 2020 ?",
            "What is the area of wheat cultivation in Ludhiana district punjab in 2020 in Rabi season ?",
            "Analyze rice production trend in Punjab over last 5 years"
        ]
        
        for i, q in enumerate(sample_questions):
            if st.button(f"Q{i+1}: {q[:30]}...", key=f"sample_{i}", use_container_width=True):
                st.session_state.current_question = q
                st.rerun()
    
    # Main content area
    if not st.session_state.data_loaded:
        # Welcome screen
        st.info("👈 Please configure API key and load data from the sidebar to begin")
        
        # Show system features
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🎯 Key Features
            - Real-time data from data.gov.in
            - Natural language queries
            - Multi-dataset correlation
            - Source citation
            """)
        
        with col2:
            st.markdown("""
            ### 📈 Analytics
            - Trend analysis
            - Comparative insights
            - Climate correlation
            - District-level granularity
            """)
        
        with col3:
            st.markdown("""
            ### 🔒 Core Values
            - Data accuracy
            - Full traceability
            - Privacy-focused
            - Open source
            """)
        
        # Show sample data preview
        st.subheader("📊 Sample Data Preview")
        st.markdown("""
        The system analyzes data from:
        - **Agriculture:** Crop production, area, yield by state/district
        - **Climate:** Rainfall patterns, monsoon data
        - **Time Series:** Multi-year trends and correlations
        """)
        
        return
    
    # Query interface
    st.subheader("🤖 Ask Your Question")
    
    # Text input
    question = st.text_area(
        "Enter your question about agriculture and climate data:",
        value=st.session_state.current_question,
        height=100,
        placeholder="e.g., Which district has highest wheat production in Punjab in Rabi season in 2020?"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        ask_button = st.button("🔍 Ask", use_container_width=True, type="primary")
    with col2:
        clear_button = st.button("🗑️ Clear History", use_container_width=True)
    
    if clear_button:
        st.session_state.chat_history = []
        st.session_state.current_question = ""
        st.rerun()
    
    # Process question
    if ask_button and question:
        if not st.session_state.query_engine:
            st.error("❌ Query engine not initialized. Please load data first.")
        else:
            with st.spinner("🔄 Analyzing your question and querying datasets..."):
                try:
                    result = st.session_state.query_engine.answer_question(question)
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        "question": question,
                        "result": result,
                        "timestamp": datetime.now()
                    })
                    
                    # Clear current question
                    st.session_state.current_question = ""
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error processing question: {str(e)}")
                    import traceback
                    with st.expander("🔍 Debug Information"):
                        st.code(traceback.format_exc())
    
    # Display chat history
    if st.session_state.chat_history:
        st.divider()
        st.subheader("📝 Query Results")
        
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(f"Q: {chat['question'][:100]}...", expanded=(i==0)):
                # Timestamp
                st.caption(f"⏰ {chat['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Answer
                st.markdown("### 📄 Answer")
                answer = chat['result'].get('answer', 'No answer generated')
                
                # Check for error messages
                if answer.startswith('⚠️') or answer.startswith('❌'):
                    st.warning(answer)
                else:
                    st.markdown(answer)
                
                # Data visualization
                if chat['result'].get('data') and chat['result']['data']:
                    st.markdown("### 📊 Data Insights")
                    try:
                        render_visualizations(chat['result']['data'])
                    except Exception as e:
                        st.error(f"Error rendering visualization: {e}")
                        with st.expander("🔍 Raw Data"):
                            st.json(chat['result']['data'])
                
                # Sources
                if chat['result'].get('sources'):
                    st.markdown("### 📚 Data Sources")
                    for source in chat['result']['sources']:
                        st.markdown(f"- {source}")
                
                st.markdown('<div class="source-tag">✅ All data sourced from data.gov.in</div>', 
                          unsafe_allow_html=True)
    
    # Footer
    st.divider()
    st.caption("💡 Tip: Try asking about specific districts, crops, years, or seasons for detailed insights!")

if __name__ == "__main__":
"""
Project Samarth - Intelligent Q&A System
Streamlit Frontend Application - FIXED VERSION
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_collector import DataCollector
from query_engine import QueryEngine  # Use the fixed version
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Project Samarth - Agriculture Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .source-tag {
        background-color: #E8F5E9;
        padding: 0.5rem;
        border-radius: 5px;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #F1F8E9;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'query_engine' not in st.session_state:
    st.session_state.query_engine = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = ""

@st.cache_resource
def load_data():
    """Load and cache data"""
    try:
        collector = DataCollector()
        return collector.get_all_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def initialize_query_engine(data, api_key):
    """Initialize query engine with LLM"""
    try:
        return QueryEngine(api_key, data)
    except Exception as e:
        st.error(f"Error initializing query engine: {e}")
        return None

def render_visualizations(data):
    """Render visualizations based on data structure"""
    
    # District-level crop data visualization
    if 'highest_district' in data:
        st.markdown("### 📍 District Analysis")
        district_data = data['highest_district']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("District", district_data.get('District', 'N/A'))
        with col2:
            st.metric("Production", f"{district_data.get('Production', 0):.0f} tonnes")
        with col3:
            st.metric("Year", district_data.get('Year', 'N/A'))
        
        # Top districts bar chart
        if 'top_districts' in data and data['top_districts']:
            top_df = pd.DataFrame(data['top_districts'])
            if not top_df.empty and 'District' in top_df.columns:
                fig = px.bar(
                    top_df, 
                    x='District', 
                    y='Production',
                    title='Top Districts by Production',
                    color='Production',
                    color_continuous_scale='Greens'
                )
                fig.update_layout(xaxis_title="District", yaxis_title="Production (tonnes)")
                st.plotly_chart(fig, use_container_width=True)
    
    # Rainfall and crops comparison with year-by-year data
    elif 'rainfall' in data and 'crops' in data:
        # Year-by-year rainfall comparison
        if 'rainfall_by_year' in data:
            st.markdown("### 📊 Year-by-Year Rainfall Comparison")
            
            rainfall_yearly = data['rainfall_by_year']
            states = list(rainfall_yearly.keys())
            
            # Create line chart for yearly comparison
            fig = go.Figure()
            
            colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0']
            for idx, state in enumerate(states):
                yearly_data = rainfall_yearly[state]
                years = list(yearly_data.keys())
                values = list(yearly_data.values())
                
                fig.add_trace(go.Scatter(
                    x=years,
                    y=values,
                    name=state,
                    mode='lines+markers',
                    line=dict(color=colors[idx % len(colors)], width=3),
                    marker=dict(size=8)
                ))
            
            fig.update_layout(
                title=f"Annual Rainfall Comparison ({data.get('year_range', 'All Years')})",
                xaxis_title="Year",
                yaxis_title="Rainfall (mm)",
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Average rainfall comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Average Rainfall")
            rf_data = data['rainfall']
            if rf_data:
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(rf_data.keys()),
                        y=list(rf_data.values()),
                        marker_color=['#4CAF50', '#2196F3', '#FF9800'],
                        text=[f"{v:.1f} mm" for v in rf_data.values()],
                        textposition='outside'
                    )
                ])
                fig.update_layout(
                    title="Average Annual Rainfall",
                    xaxis_title="State",
                    yaxis_title="Rainfall (mm)",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🌾 Top Crops Production")
            # Crop production comparison
            crop_data = data['crops']
            if crop_data:
                states = list(crop_data.keys())
                if states:
                    # Create grouped bar chart for crops
                    all_crops = set()
                    for state_crops in crop_data.values():
                        all_crops.update(state_crops.keys())
                    
                    fig = go.Figure()
                    colors = ['#66BB6A', '#42A5F5', '#FFA726']
                    
                    for idx, state in enumerate(states[:2]):  # Show first 2 states
                        state_crops = crop_data[state]
                        fig.add_trace(go.Bar(
                            name=state,
                            x=list(state_crops.keys()),
                            y=list(state_crops.values()),
                            marker_color=colors[idx]
                        ))
                    
                    fig.update_layout(
                        title=f"Crop Production Comparison",
                        xaxis_title="Crop",
                        yaxis_title="Production (tonnes)",
                        barmode='group'
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    # Trend analysis
    elif 'crop_trend' in data:
        crop_trend = pd.Series(data['crop_trend'])
        rain_trend = pd.Series(data.get('rainfall_trend', {}))
        
        fig = go.Figure()
        
        # Add production line
        fig.add_trace(go.Scatter(
            x=crop_trend.index,
            y=crop_trend.values,
            name='Production',
            line=dict(color='#4CAF50', width=3),
            mode='lines+markers'
        ))
        
        # Add rainfall line if available
        if not rain_trend.empty:
            fig.add_trace(go.Scatter(
                x=rain_trend.index,
                y=rain_trend.values,
                name='Rainfall',
                yaxis='y2',
                line=dict(color='#2196F3', width=3),
                mode='lines+markers'
            ))
            
            fig.update_layout(
                title='Production & Rainfall Trend',
                xaxis_title='Year',
                yaxis_title='Production (tonnes)',
                yaxis2=dict(
                    title='Rainfall (mm)', 
                    overlaying='y', 
                    side='right'
                ),
                hovermode='x unified'
            )
        else:
            fig.update_layout(
                title='Production Trend',
                xaxis_title='Year',
                yaxis_title='Production (tonnes)',
                hovermode='x unified'
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show correlation if available
        if 'correlation' in data:
            corr = data['correlation']
            col1, col2, col3 = st.columns(3)
            with col2:
                st.metric(
                    "Correlation Coefficient", 
                    f"{corr:.3f}",
                    help="Correlation between production and rainfall"
                )

def main():
    # Header
    st.markdown('<h1 class="main-header">🌾 Project Samarth</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Intelligent Q&A System for Agriculture & Climate Data</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key input
        api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            help="Get your free API key from https://aistudio.google.com/app/apikey"
        )
        
        if not api_key:
            st.warning("Please enter your Gemini API key to continue")
            st.info("📌 Get free API key: [Google AI Studio](https://aistudio.google.com/app/apikey)")
        else:
            # Load data button
            if st.button("🔄 Load Data", use_container_width=True):
                with st.spinner("Loading datasets from data.gov.in..."):
                    data = load_data()
                    if data:
                        st.session_state.data = data
                        engine = initialize_query_engine(data, api_key)
                        if engine:
                            st.session_state.query_engine = engine
                            st.session_state.data_loaded = True
                            st.success("✅ Data loaded successfully!")
                        else:
                            st.error("❌ Failed to initialize query engine")
                    else:
                        st.error("❌ Failed to load data")
        
        st.divider()
        
        # Data statistics
        if st.session_state.data_loaded:
            st.subheader("📊 Data Statistics")
            data = st.session_state.data
            
            st.metric("Crop Records", len(data['crop_production']))
            st.metric("Rainfall Records", len(data['rainfall']))
            st.metric("States", data['crop_production']['State'].nunique())
            st.metric("Crops", data['crop_production']['Crop'].nunique())
            st.metric("Years", f"{data['crop_production']['Year'].min()}-{data['crop_production']['Year'].max()}")
        
        st.divider()
        
        # Sample questions
        st.subheader("💡 Sample Questions")
        sample_questions = [
            "What is the area of  rice cultivation in Amritsar district punjab in 2020 ?",
            "Which district has highest wheat production in Punjab ?",
            "Which district has highest wheat production in Punjab in Rabi season in 2020 ?",
            "What is the area of wheat cultivation in Ludhiana district punjab in 2020 in Rabi season ?",
            "Analyze rice production trend in Punjab over last 5 years"
        ]
        
        for i, q in enumerate(sample_questions):
            if st.button(f"Q{i+1}: {q[:30]}...", key=f"sample_{i}", use_container_width=True):
                st.session_state.current_question = q
                st.rerun()
    
    # Main content area
    if not st.session_state.data_loaded:
        # Welcome screen
        st.info("👈 Please configure API key and load data from the sidebar to begin")
        
        # Show system features
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🎯 Key Features
            - Real-time data from data.gov.in
            - Natural language queries
            - Multi-dataset correlation
            - Source citation
            """)
        
        with col2:
            st.markdown("""
            ### 📈 Analytics
            - Trend analysis
            - Comparative insights
            - Climate correlation
            - District-level granularity
            """)
        
        with col3:
            st.markdown("""
            ### 🔒 Core Values
            - Data accuracy
            - Full traceability
            - Privacy-focused
            - Open source
            """)
        
        # Show sample data preview
        st.subheader("📊 Sample Data Preview")
        st.markdown("""
        The system analyzes data from:
        - **Agriculture:** Crop production, area, yield by state/district
        - **Climate:** Rainfall patterns, monsoon data
        - **Time Series:** Multi-year trends and correlations
        """)
        
        return
    
    # Query interface
    st.subheader("🤖 Ask Your Question")
    
    # Text input
    question = st.text_area(
        "Enter your question about agriculture and climate data:",
        value=st.session_state.current_question,
        height=100,
        placeholder="e.g., Which district has highest wheat production in Punjab in Rabi season in 2020?"
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        ask_button = st.button("🔍 Ask", use_container_width=True, type="primary")
    with col2:
        clear_button = st.button("🗑️ Clear History", use_container_width=True)
    
    if clear_button:
        st.session_state.chat_history = []
        st.session_state.current_question = ""
        st.rerun()
    
    # Process question
    if ask_button and question:
        if not st.session_state.query_engine:
            st.error("❌ Query engine not initialized. Please load data first.")
        else:
            with st.spinner("🔄 Analyzing your question and querying datasets..."):
                try:
                    result = st.session_state.query_engine.answer_question(question)
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        "question": question,
                        "result": result,
                        "timestamp": datetime.now()
                    })
                    
                    # Clear current question
                    st.session_state.current_question = ""
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error processing question: {str(e)}")
                    import traceback
                    with st.expander("🔍 Debug Information"):
                        st.code(traceback.format_exc())
    
    # Display chat history
    if st.session_state.chat_history:
        st.divider()
        st.subheader("📝 Query Results")
        
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(f"Q: {chat['question'][:100]}...", expanded=(i==0)):
                # Timestamp
                st.caption(f"⏰ {chat['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Answer
                st.markdown("### 📄 Answer")
                answer = chat['result'].get('answer', 'No answer generated')
                
                # Check for error messages
                if answer.startswith('⚠️') or answer.startswith('❌'):
                    st.warning(answer)
                else:
                    st.markdown(answer)
                
                # Data visualization
                if chat['result'].get('data') and chat['result']['data']:
                    st.markdown("### 📊 Data Insights")
                    try:
                        render_visualizations(chat['result']['data'])
                    except Exception as e:
                        st.error(f"Error rendering visualization: {e}")
                        with st.expander("🔍 Raw Data"):
                            st.json(chat['result']['data'])
                
                # Sources
                if chat['result'].get('sources'):
                    st.markdown("### 📚 Data Sources")
                    for source in chat['result']['sources']:
                        st.markdown(f"- {source}")
                
                st.markdown('<div class="source-tag">✅ All data sourced from data.gov.in</div>', 
                          unsafe_allow_html=True)
    
    # Footer
    st.divider()
    st.caption("💡 Tip: Try asking about specific districts, crops, years, or seasons for detailed insights!")

if __name__ == "__main__":
    main()
