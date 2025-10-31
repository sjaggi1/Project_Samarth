"""
Project Samarth - Intelligent Q&A System
Streamlit Frontend Application - Updated Version (with Manual Query Trigger)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_collector import DataCollector
from query_engine import QueryEngine
from datetime import datetime
import os

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
for key, default in {
    'data_loaded': False,
    'query_engine': None,
    'chat_history': [],
    'current_question': "",
    'user_input': "",
    'data': None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


@st.cache_resource
def load_data():
    """Load and cache data"""
    try:
        collector = DataCollector()
        return collector.get_all_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


@st.cache_resource
def get_query_engine(api_key, data):
    """Cache the QueryEngine to speed up responses"""
    try:
        return QueryEngine(api_key, data)
    except Exception as e:
        st.error(f"Error initializing query engine: {e}")
        return None


def render_visualizations(data):
    """Render dynamic charts based on the returned data"""
    if not data:
        return

    # District-level analysis
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

    # Rainfall & crops
    elif 'rainfall' in data and 'crops' in data:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📈 Average Rainfall")
            rf_data = data['rainfall']
            if rf_data:
                fig = go.Figure(data=[go.Bar(
                    x=list(rf_data.keys()),
                    y=list(rf_data.values()),
                    marker_color=['#4CAF50', '#2196F3', '#FF9800'],
                    text=[f"{v:.1f} mm" for v in rf_data.values()],
                    textposition='outside'
                )])
                fig.update_layout(
                    title="Average Annual Rainfall",
                    xaxis_title="State",
                    yaxis_title="Rainfall (mm)",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown("### 🌾 Top Crops Production")
            crop_data = data['crops']
            if crop_data:
                states = list(crop_data.keys())
                fig = go.Figure()
                colors = ['#66BB6A', '#42A5F5', '#FFA726']
                for idx, state in enumerate(states[:2]):
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

    # Crop production trend
    elif 'crop_trend' in data:
        crop_trend = pd.Series(data['crop_trend'])
        rain_trend = pd.Series(data.get('rainfall_trend', {}))
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=crop_trend.index,
            y=crop_trend.values,
            name='Production',
            line=dict(color='#4CAF50', width=3),
            mode='lines+markers'
        ))
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
                )
            )
        st.plotly_chart(fig, use_container_width=True)
        if 'correlation' in data:
            corr = data['correlation']
            st.metric("Correlation Coefficient", f"{corr:.3f}",
                      help="Correlation between production and rainfall")


def main():
    st.markdown('<h1 class="main-header">🌾 Project Samarth</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Intelligent Q&A System for Agriculture & Climate Data</p>', unsafe_allow_html=True)

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        api_key = st.text_input(
            "Google Gemini API Key",
            type="password",
            help="Get your API key from https://aistudio.google.com/app/apikey"
        )

        if not api_key:
            st.warning("Please enter your Gemini API key to continue")
            st.info("📌 Get free API key: [Google AI Studio](https://aistudio.google.com/app/apikey)")
        else:
            if st.button("🔄 Load Data", use_container_width=True):
                with st.spinner("Loading datasets..."):
                    data = load_data()
                    if data:
                        st.session_state.data = data
                        engine = get_query_engine(api_key, data)
                        if engine:
                            st.session_state.query_engine = engine
                            st.session_state.data_loaded = True
                            st.success("✅ Data loaded successfully!")
                        else:
                            st.error("❌ Failed to initialize query engine")
                    else:
                        st.error("❌ Failed to load data")

        st.divider()

        if st.session_state.data_loaded:
            data = st.session_state.data
            st.subheader("📊 Data Statistics")
            st.metric("Crop Records", len(data['crop_production']))
            st.metric("Rainfall Records", len(data['rainfall']))
            st.metric("States", data['crop_production']['State'].nunique())
            st.metric("Crops", data['crop_production']['Crop'].nunique())
            st.metric("Years", f"{data['crop_production']['Year'].min()}-{data['crop_production']['Year'].max()}")

        st.divider()

        # ✅ Updated Sidebar Sample Questions Section
        st.subheader("💡 Sample Questions")
        sample_questions = [
            "What is the area of rice cultivation in Amritsar district Punjab in 2020?",
            "Which district has highest wheat production in Punjab?",
            "Which district has highest wheat production in Punjab in Rabi season in 2020?",
            "What is the area of wheat cultivation in Ludhiana district Punjab in 2020 in Rabi season?",
            "Analyze rice production trend in Punjab over last 5 years"
        ]
        for i, q in enumerate(sample_questions):
            if st.sidebar.button(f"Q{i+1}: {q[:30]}...", key=f"sample_sidebar_{i}", use_container_width=True):
                # Only set question — do not query yet
                st.session_state.current_question = q
                st.session_state.user_input = q

    # Main content
    if not st.session_state.data_loaded:
        st.info("👈 Configure your API key and load data to begin.")
        return

    # ✅ Input box for user question
    st.subheader("🤖 Ask Your Question")
    user_query = st.text_input(
        "Ask your question here:",
        value=st.session_state.get("user_input", ""),
        key="user_query"
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        ask_button = st.button("🔍 Ask", use_container_width=True, type="primary")
    with col2:
        clear_button = st.button("🗑️ Clear History", use_container_width=True)

    if clear_button:
        st.session_state.chat_history = []
        st.session_state.user_input = ""
        st.session_state.current_question = ""
        st.experimental_rerun()

    if ask_button:
        query = user_query.strip()
        if not query:
            st.warning("Please enter a question before asking.")
        elif not st.session_state.query_engine:
            st.error("❌ Query engine not initialized. Load data first.")
        else:
            with st.spinner("🔎 Processing your question..."):
                result = st.session_state.query_engine.answer_question(query)
                st.session_state.chat_history.append({
                    "question": query,
                    "result": result,
                    "timestamp": datetime.now()
                })
                st.session_state.user_input = ""
                st.experimental_rerun()

    # Display results
    if st.session_state.chat_history:
        st.divider()
        st.subheader("📝 Query Results")
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(f"Q: {chat['question'][:100]}...", expanded=(i == 0)):
                st.caption(f"⏰ {chat['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown("### 📄 Answer")
                st.markdown(chat['result'].get('answer', 'No answer generated'))
                if chat['result'].get('data'):
                    st.markdown("### 📊 Data Insights")
                    render_visualizations(chat['result']['data'])
                if chat['result'].get('sources'):
                    st.markdown("### 📚 Sources")
                    for s in chat['result']['sources']:
                        st.markdown(f"- {s}")
                st.markdown('<div class="source-tag">✅ Data sourced from data.gov.in</div>', unsafe_allow_html=True)

    # Footer
    st.divider()
    st.caption("💡 Tip: Click a sample question to fill it, then press 'Ask' to run the query!")


if __name__ == "__main__":
    main()
