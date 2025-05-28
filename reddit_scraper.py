import requests
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
import json
import re
from urllib.parse import quote_plus
import logging

class RedditScraper:
    """
    Comprehensive Reddit scraper using multiple strategies for robust data collection
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for debugging and monitoring"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def init_browser(self):
        """Initialize headless Chrome browser"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.logger.info("Browser initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize browser: {e}")
                raise
    
    def close_browser(self):
        """Close browser and cleanup resources"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def search_mentions(self, search_term, time_filter="week", sort="relevance", 
                       limit=200, include_comments=False, progress_callback=None):
        """
        Main search function that combines multiple scraping strategies
        """
        all_results = []
        
        try:
            # Strategy 1: Reddit JSON API
            self.logger.info("Attempting Reddit JSON API search...")
            if progress_callback:
                progress_callback(0.1)
            
            json_results = self._search_via_json_api(search_term, time_filter, sort, limit // 2)
            all_results.extend(json_results)
            
            if progress_callback:
                progress_callback(0.4)
            
            # Strategy 2: Browser automation for dynamic content
            self.logger.info("Attempting browser-based search...")
            browser_results = self._search_via_browser(search_term, time_filter, sort, limit // 2)
            all_results.extend(browser_results)
            
            if progress_callback:
                progress_callback(0.7)
            
            # Strategy 3: Multiple subreddit search
            if len(all_results) < limit // 2:
                self.logger.info("Performing targeted subreddit search...")
                subreddit_results = self._search_multiple_subreddits(search_term, limit // 4)
                all_results.extend(subreddit_results)
            
            if progress_callback:
                progress_callback(0.9)
            
            # Remove duplicates and sort
            seen_ids = set()
            unique_results = []
            for result in all_results:
                if result.get('id') not in seen_ids:
                    seen_ids.add(result.get('id'))
                    unique_results.append(result)
            
            # Sort by creation date (newest first)
            unique_results.sort(key=lambda x: x.get('created_utc', 0), reverse=True)
            
            self.logger.info(f"Found {len(unique_results)} unique results")
            return unique_results[:limit]
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return all_results
        
        finally:
            self.close_browser()
    
    def _search_via_json_api(self, search_term, time_filter, sort, limit):
        """Search using Reddit's JSON API"""
        results = []
        
        try:
            # Search across all of Reddit
            url = f"https://www.reddit.com/search.json"
            params = {
                'q': search_term,
                'sort': sort,
                't': time_filter,
                'limit': min(limit, 100),
                'type': 'link'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and 'children' in data['data']:
                for post in data['data']['children']:
                    post_data = post['data']
                    results.append(self._extract_post_data(post_data))
                    
            self.logger.info(f"JSON API returned {len(results)} results")
            
        except Exception as e:
            self.logger.warning(f"JSON API search failed: {e}")
        
        return results
    
    def _search_via_browser(self, search_term, time_filter, sort, limit):
        """Search using browser automation for dynamic content"""
        results = []
        
        try:
            self.init_browser()
            
            # Navigate to Reddit search
            search_url = f"https://www.reddit.com/search/?q={quote_plus(search_term)}&type=link&sort={sort}&t={time_filter}"
            self.driver.get(search_url)
            
            # Wait for content to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Scroll to load more content
            self._scroll_to_load_content(3)
            
            # Extract post data
            posts = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="post-container"]')
            
            for post in posts[:limit]:
                try:
                    post_data = self._extract_browser_post_data(post)
                    if post_data:
                        results.append(post_data)
                except Exception as e:
                    self.logger.debug(f"Failed to extract post data: {e}")
                    continue
            
            self.logger.info(f"Browser search returned {len(results)} results")
            
        except Exception as e:
            self.logger.warning(f"Browser search failed: {e}")
        
        return results
    
    def _search_multiple_subreddits(self, search_term, limit):
        """Search across multiple relevant subreddits"""
        results = []
        
        # Common subreddits for business/tech/general discussion
        target_subreddits = [
            'technology', 'business', 'news', 'worldnews', 'stocks',
            'investing', 'entrepreneur', 'startups', 'tech', 'gadgets'
        ]
        
        posts_per_subreddit = max(1, limit // len(target_subreddits))
        
        for subreddit in target_subreddits:
            try:
                subreddit_results = self._search_subreddit_json(search_term, subreddit, posts_per_subreddit)
                results.extend(subreddit_results)
                
                # Rate limiting
                time.sleep(random.uniform(0.5, 1.0))
                
            except Exception as e:
                self.logger.debug(f"Failed to search r/{subreddit}: {e}")
                continue
        
        return results
    
    def _search_subreddit_json(self, search_term, subreddit, limit):
        """Search a specific subreddit using JSON API"""
        results = []
        
        try:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {
                'q': search_term,
                'restrict_sr': 'on',
                'sort': 'relevance',
                't': 'week',
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and 'children' in data['data']:
                for post in data['data']['children']:
                    post_data = post['data']
                    results.append(self._extract_post_data(post_data))
            
        except Exception as e:
            self.logger.debug(f"Subreddit search failed for r/{subreddit}: {e}")
        
        return results
    
    def _extract_post_data(self, post_data):
        """Extract and normalize post data from Reddit API response"""
        return {
            'id': post_data.get('id', ''),
            'title': post_data.get('title', ''),
            'selftext': post_data.get('selftext', ''),
            'author': post_data.get('author', '[deleted]'),
            'subreddit': post_data.get('subreddit', ''),
            'score': post_data.get('score', 0),
            'upvote_ratio': post_data.get('upvote_ratio', 0.0),
            'num_comments': post_data.get('num_comments', 0),
            'created_utc': post_data.get('created_utc', 0),
            'url': post_data.get('url', ''),
            'permalink': f"https://www.reddit.com{post_data.get('permalink', '')}",
            'domain': post_data.get('domain', ''),
            'is_self': post_data.get('is_self', False)
        }
    
    def _extract_browser_post_data(self, post_element):
        """Extract post data from browser-rendered element"""
        try:
            # Extract title
            title_elem = post_element.find_element(By.CSS_SELECTOR, 'h3')
            title = title_elem.text if title_elem else 'N/A'
            
            # Extract subreddit
            subreddit_elem = post_element.find_element(By.CSS_SELECTOR, '[data-testid="subreddit-name"]')
            subreddit = subreddit_elem.text.replace('r/', '') if subreddit_elem else 'unknown'
            
            # Extract score
            score_elem = post_element.find_element(By.CSS_SELECTOR, '[data-testid="post-vote-count-unvoted"]')
            score = self._parse_score(score_elem.text) if score_elem else 0
            
            # Extract comment count
            comment_elem = post_element.find_element(By.CSS_SELECTOR, '[data-testid="post-comment-count"]')
            num_comments = self._parse_comment_count(comment_elem.text) if comment_elem else 0
            
            # Extract permalink
            link_elem = post_element.find_element(By.CSS_SELECTOR, 'a[data-testid="post-title"]')
            permalink = link_elem.get_attribute('href') if link_elem else ''
            
            return {
                'id': f"browser_{random.randint(100000, 999999)}",
                'title': title,
                'subreddit': subreddit,
                'score': score,
                'num_comments': num_comments,
                'permalink': permalink,
                'created_utc': int(time.time()),  # Approximate
                'author': 'N/A',
                'selftext': '',
                'upvote_ratio': 0.0,
                'url': permalink,
                'domain': 'reddit.com',
                'is_self': True
            }
            
        except Exception as e:
            self.logger.debug(f"Failed to extract browser post data: {e}")
            return None
    
    def _scroll_to_load_content(self, num_scrolls=3):
        """Scroll page to trigger lazy loading"""
        for i in range(num_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
    
    def _parse_score(self, score_text):
        """Parse score text to integer"""
        try:
            score_text = score_text.lower().replace(',', '')
            if 'k' in score_text:
                return int(float(score_text.replace('k', '')) * 1000)
            return int(score_text)
        except:
            return 0
    
    def _parse_comment_count(self, comment_text):
        """Parse comment count text to integer"""
        try:
            numbers = re.findall(r'\d+', comment_text.replace(',', ''))
            return int(numbers[0]) if numbers else 0
        except:
            return 0
