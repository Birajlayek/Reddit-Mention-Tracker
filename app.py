import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from reddit_scraper import RedditScraper
import asyncio
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Reddit Mention Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #ff4b4b, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff4b4b;
    }
    .search-section {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">Reddit Mention Tracker</h1>', unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        max_posts = st.slider("Maximum posts to analyze", 50, 500, 200)
        time_filter = st.selectbox("Time Filter", ["week", "day", "month"], index=0)
        sort_by = st.selectbox("Sort by", ["relevance", "hot", "new", "top"], index=0)
        include_comments = st.checkbox("Include comment analysis", value=True)
        
        st.header("📋 Search Tips")
        st.info("""
        • Use quotes for exact phrases: "Company Name"
        • Use OR for multiple terms: Tesla OR SpaceX
        • Be specific to reduce noise
        • Check results for relevance
        """)
    
    # Main search interface
    with st.container():
        st.markdown('<div class="search-section">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input(
                "🔍 Enter company or person name to track:",
                placeholder="e.g., Tesla, Elon Musk, Microsoft",
                help="Enter the entity you want to track mentions for on Reddit"
            )
        
        with col2:
            st.write("")  # Spacing
            search_button = st.button("🚀 Start Search", type="primary", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Search execution and results
    if search_button and search_term:
        execute_search(search_term, max_posts, time_filter, sort_by, include_comments)
    
    # Display sample data if no search performed
    if not search_term or not search_button:
        display_sample_dashboard()

def execute_search(search_term, max_posts, time_filter, sort_by, include_comments):
    """Execute the Reddit search and display results"""
    
    with st.spinner(f"🔍 Searching Reddit for mentions of '{search_term}'..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize scraper
            scraper = RedditScraper()
            
            # Update progress
            progress_bar.progress(20)
            status_text.text("Initializing browser...")
            
            # Perform search
            results = scraper.search_mentions(
                search_term=search_term,
                time_filter=time_filter,
                sort=sort_by,
                limit=max_posts,
                include_comments=include_comments,
                progress_callback=lambda p: progress_bar.progress(20 + int(p * 0.7))
            )
            
            progress_bar.progress(95)
            status_text.text("Processing results...")
            
            if results and len(results) > 0:
                # Convert to DataFrame
                df = pd.DataFrame(results)
                df['created_date'] = pd.to_datetime(df['created_utc'], unit='s')
                
                # Filter last 7 days
                seven_days_ago = datetime.now() - timedelta(days=7)
                recent_df = df[df['created_date'] >= seven_days_ago]
                
                progress_bar.progress(100)
                status_text.text("✅ Search completed!")
                
                # Display results
                display_results(search_term, recent_df, df)
                
            else:
                st.warning(f"No mentions found for '{search_term}' in the specified timeframe.")
                
        except Exception as e:
            st.error(f"An error occurred during search: {str(e)}")
            st.info("This might be due to rate limiting or network issues. Please try again in a few minutes.")
        
        finally:
            progress_bar.empty()
            status_text.empty()

def display_results(search_term, recent_df, full_df):
    """Display search results with analytics"""
    
    st.header(f"📊 Results for '{search_term}'")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Mentions (7 days)",
            len(recent_df),
            delta=f"{len(recent_df) - len(full_df[full_df['created_date'] >= datetime.now() - timedelta(days=14)]) + len(recent_df)} vs prev week"
        )
    
    with col2:
        avg_score = recent_df['score'].mean() if len(recent_df) > 0 else 0
        st.metric("Average Score", f"{avg_score:.1f}")
    
    with col3:
        total_comments = recent_df['num_comments'].sum() if len(recent_df) > 0 else 0
        st.metric("Total Comments", total_comments)
    
    with col4:
        unique_subreddits = recent_df['subreddit'].nunique() if len(recent_df) > 0 else 0
        st.metric("Subreddits", unique_subreddits)
    
    if len(recent_df) > 0:
        # Timeline chart
        st.subheader("📈 Mention Timeline")
        daily_counts = recent_df.groupby(recent_df['created_date'].dt.date).size().reset_index()
        daily_counts.columns = ['Date', 'Mentions']
        
        fig_timeline = px.line(daily_counts, x='Date', y='Mentions', 
                              title="Daily Mentions Over Last 7 Days")
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Subreddit distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top Subreddits")
            subreddit_counts = recent_df['subreddit'].value_counts().head(10)
            fig_subreddits = px.bar(x=subreddit_counts.values, y=subreddit_counts.index,
                                   orientation='h', title="Mentions by Subreddit")
            st.plotly_chart(fig_subreddits, use_container_width=True)
        
        with col2:
            st.subheader("💬 Engagement Distribution")
            fig_engagement = px.scatter(recent_df, x='score', y='num_comments',
                                       hover_data=['title', 'subreddit'],
                                       title="Score vs Comments")
            st.plotly_chart(fig_engagement, use_container_width=True)
        
        # Recent posts table
        st.subheader("📝 Recent Posts")
        display_df = recent_df[['title', 'subreddit', 'score', 'num_comments', 'created_date']].copy()
        display_df['created_date'] = display_df['created_date'].dt.strftime('%Y-%m-%d %H:%M')
        display_df = display_df.sort_values('created_date', ascending=False)
        
        st.dataframe(
            display_df,
            column_config={
                "title": st.column_config.TextColumn("Title", width="large"),
                "subreddit": st.column_config.TextColumn("Subreddit", width="small"),
                "score": st.column_config.NumberColumn("Score", format="%d"),
                "num_comments": st.column_config.NumberColumn("Comments", format="%d"),
                "created_date": st.column_config.TextColumn("Created", width="small")
            },
            use_container_width=True,
            height=400
        )
        
        # Export functionality
        csv = recent_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"reddit_mentions_{search_term}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def display_sample_dashboard():
    """Display sample data when no search is performed"""
    st.header("📊 Sample Dashboard")
    st.info("Enter a search term above to track real Reddit mentions!")
    
    # Sample metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sample Mentions", "42", delta="↑12%")
    with col2:
        st.metric("Average Score", "156.3", delta="↑8.2%")
    with col3:
        st.metric("Total Comments", "2,847", delta="↑15%")
    with col4:
        st.metric("Subreddits", "28", delta="↑3")
    
    # Sample chart
    sample_data = pd.DataFrame({
        'Date': pd.date_range(start='2024-05-22', periods=7),
        'Mentions': [5, 12, 8, 15, 22, 18, 10]
    })
    
    fig = px.line(sample_data, x='Date', y='Mentions', 
                  title="Sample: Daily Mentions Timeline")
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
