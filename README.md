# Reddit Mention Tracker

A comprehensive web application for tracking mentions of companies or individuals on Reddit using advanced web scraping techniques.

## Features

- 🔍 **Multi-Strategy Scraping**: Combines Reddit JSON API with headless browser automation
- 📊 **Rich Analytics**: Provides detailed metrics and visualizations for the last 7 days
- 🚀 **Real-time Search**: Live search with progress tracking
- 📈 **Interactive Dashboards**: Timeline charts, engagement metrics, and subreddit analysis
- 💾 **Data Export**: Download results as CSV for further analysis
- 🛡️ **Rate Limiting**: Built-in protections against bot detection

## Quick Start

### Local Installation

1. **Clone the repository:**
git clone https://github.com/yourusername/reddit-mention-tracker.git
cd reddit-mention-tracker

text

2. **Install dependencies:**
pip install -r requirements.txt

text

3. **Install Chrome WebDriver:**
The app will automatically download the appropriate driver
Or install manually from: https://chromedriver.chromium.org/
text

4. **Run the application:**
streamlit run app.py

text

5. **Open your browser** and navigate to `http://localhost:8501`

### Docker Deployment

Build the image
docker build -t reddit-tracker .

Run the container
docker run -p 8501:8501 reddit-tracker

text

## Usage

1. **Enter Search Term**: Input the company or person name you want to track
2. **Configure Settings**: Adjust search parameters in the sidebar
3. **Start Search**: Click the search button to begin crawling
4. **View Results**: Analyze the comprehensive dashboard with metrics and charts
5. **Export Data**: Download results for offline analysis

## Architecture

### Design Decisions

- **Multi-Strategy Approach**: Combines Reddit's JSON API with browser automation for maximum coverage
- **Graceful Degradation**: Falls back to alternative methods if primary strategies fail
- **Rate Limiting**: Implements delays and rotation to avoid bot detection
- **Responsive UI**: Streamlit provides fast, interactive interface development

### Technical Stack

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python with Selenium for browser automation
- **Data Processing**: Pandas for analytics and data manipulation
- **Visualization**: Plotly for interactive charts
- **Web Scraping**: Multi-strategy approach using requests and Selenium

### Scalability Considerations

- **Proxy Integration**: Ready for proxy rotation to handle larger volumes
- **Database Support**: Easy to extend with database storage for persistence
- **Microservices**: Architecture supports splitting into separate services
- **Caching**: Can add Redis/Memcached for improved performance

## Search Strategies

1. **Reddit JSON API**: Fast, reliable access to public data
2. **Browser Automation**: Handles JavaScript-heavy content and anti-bot measures
3. **Multi-Subreddit Search**: Targeted searches across relevant communities
4. **Fallback Mechanisms**: Ensures data collection even if primary methods fail

## Rate Limiting & Ethics

- Implements respectful delays between requests
- Uses realistic browser headers and user agents
- Respects robots.txt and terms of service
- Includes configurable rate limiting options

## Future Enhancements

- **Real-time Monitoring**: WebSocket-based live updates
- **Sentiment Analysis**: NLP integration for mention sentiment
- **Alert System**: Email/SMS notifications for mention spikes
- **API Endpoints**: RESTful API for programmatic access
- **Multi-Platform**: Extend to Twitter, LinkedIn, and other platforms

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and research purposes. Please ensure compliance with Reddit's Terms of Service and robots.txt when using this application.
