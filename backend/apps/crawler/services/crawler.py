"""
Web Crawler

BFS crawler for Coventry University publications with robots.txt compliance.
"""

import time
import logging
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
from collections import deque

import requests
from bs4 import BeautifulSoup
from django.utils import timezone

from apps.search.models import Author, Publication

logger = logging.getLogger(__name__)


class RobotsTxtChecker:
    """
    Checks robots.txt compliance for crawling.
    """
    
    def __init__(self, base_url: str, user_agent: str = 'IRSearchBot/1.0'):
        self.base_url = base_url
        self.user_agent = user_agent
        self.disallowed_paths = []
        self.crawl_delay = 1
        self._parse_robots_txt()
    
    def _parse_robots_txt(self):
        """Parse robots.txt from the domain."""
        try:
            parsed = urlparse(self.base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            response = requests.get(robots_url, timeout=10)
            if response.status_code == 200:
                lines = response.text.split('\n')
                current_agent = None
                
                for line in lines:
                    line = line.strip().lower()
                    
                    if line.startswith('user-agent:'):
                        agent = line.split(':', 1)[1].strip()
                        current_agent = agent if agent in ['*', self.user_agent.lower()] else None
                    
                    elif current_agent and line.startswith('disallow:'):
                        path = line.split(':', 1)[1].strip()
                        if path:
                            self.disallowed_paths.append(path)
                    
                    elif current_agent and line.startswith('crawl-delay:'):
                        try:
                            self.crawl_delay = int(line.split(':', 1)[1].strip())
                        except ValueError:
                            pass
                
                logger.info(f"Parsed robots.txt: {len(self.disallowed_paths)} disallowed paths, delay: {self.crawl_delay}s")
                
        except Exception as e:
            logger.warning(f"Could not fetch robots.txt: {e}")
    
    def is_allowed(self, url: str) -> bool:
        """Check if a URL is allowed to be crawled."""
        parsed = urlparse(url)
        path = parsed.path
        
        for disallowed in self.disallowed_paths:
            if path.startswith(disallowed):
                return False
        
        return True
    
    def get_crawl_delay(self) -> int:
        """Get the crawl delay in seconds."""
        return max(1, self.crawl_delay)


class PublicationCrawler:
    """
    BFS crawler for Coventry University publications.
    
    Target URL: https://pureportal.coventry.ac.uk/en/organisations/
    ics-research-centre-for-computational-science-and-mathematical-mo/publications/
    """
    
    BASE_URL = "https://pureportal.coventry.ac.uk/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo/publications/"
    
    def __init__(self, max_pages: Optional[int] = None):
        self.base_url = self.BASE_URL
        self.max_pages = max_pages
        self.user_agent = 'IRSearchBot/1.0 (Academic Project; Coventry University)'
        self.headers = {'User-Agent': self.user_agent}
        self.robots_checker = RobotsTxtChecker(self.base_url, self.user_agent)
        self.visited_urls = set()
        self.publications_found = []
    
    def crawl(self) -> Dict:
        """
        Perform BFS crawl of publications.
        
        Returns:
            Dictionary with crawl statistics
        """
        logger.info(f"Starting BFS crawl from {self.base_url}")
        start_time = timezone.now()
        
        # BFS queue
        queue = deque([self.base_url])
        pages_crawled = 0
        new_publications = 0
        
        has_limit = self.max_pages is not None and self.max_pages > 0

        while queue and (not has_limit or pages_crawled < self.max_pages):
            url = queue.popleft()
            
            if url in self.visited_urls:
                continue
            
            if not self.robots_checker.is_allowed(url):
                logger.info(f"Skipping disallowed URL: {url}")
                continue
            
            self.visited_urls.add(url)
            
            try:
                logger.info(f"Crawling: {url}")
                publications, next_pages = self._crawl_page(url)
                
                for pub_data in publications:
                    if self._save_publication(pub_data):
                        new_publications += 1
                
                # Add pagination links to queue
                for next_url in next_pages:
                    if next_url not in self.visited_urls:
                        queue.append(next_url)
                
                pages_crawled += 1
                
                # Polite crawling delay
                time.sleep(self.robots_checker.get_crawl_delay())
                
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
        
        duration = (timezone.now() - start_time).total_seconds()
        
        result = {
            'pages_crawled': pages_crawled,
            'new_publications': new_publications,
            'total_urls_visited': len(self.visited_urls),
            'duration_seconds': duration
        }
        
        logger.info(f"Crawl complete: {result}")
        return result
    
    def _crawl_page(self, url: str) -> tuple:
        """
        Crawl a single page and extract publications.
        
        Returns:
            Tuple of (publications_list, next_page_urls)
        """
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        publications = []
        next_pages = []
        
        # Find publication entries
        pub_items = soup.find_all('li', class_='list-result-item')
        
        for item in pub_items:
            pub_data = self._extract_publication(item)
            if pub_data:
                publications.append(pub_data)
        
        # Find pagination links
        pagination = soup.find('nav', class_='pages')
        if pagination:
            for link in pagination.find_all('a'):
                href = link.get('href')
                if href:
                    full_url = urljoin(url, href)
                    next_pages.append(full_url)
        
        return publications, next_pages
    
    def _extract_publication(self, item) -> Optional[Dict]:
        """Extract publication data from a list item."""
        try:
            # Title and link
            title_elem = item.find('h3', class_='title')
            if not title_elem:
                return None
            
            link_elem = title_elem.find('a')
            title = link_elem.get_text(strip=True) if link_elem else title_elem.get_text(strip=True)
            link = link_elem.get('href', '') if link_elem else ''
            
            if link and not link.startswith('http'):
                link = urljoin(self.base_url, link)
            
            # Authors
            authors = []
            authors_elem = item.find('span', class_='relations')
            if authors_elem:
                for author_link in authors_elem.find_all('a'):
                    author_name = author_link.get_text(strip=True)
                    author_url = author_link.get('href', '')
                    if author_url and not author_url.startswith('http'):
                        author_url = urljoin(self.base_url, author_url)
                    authors.append({'name': author_name, 'url': author_url})
            
            # Date
            date_elem = item.find('span', class_='date')
            published_date = date_elem.get_text(strip=True) if date_elem else ''
            
            # Abstract (may need separate request)
            abstract = ''
            
            return {
                'title': title,
                'link': link,
                'authors': authors,
                'published_date': published_date,
                'abstract': abstract
            }
            
        except Exception as e:
            logger.error(f"Error extracting publication: {e}")
            return None
    
    def _save_publication(self, pub_data: Dict) -> bool:
        """
        Save a publication to the database.
        
        Returns:
            True if a new publication was created, False if it already exists
        """
        try:
            # Check if publication already exists
            existing = Publication.objects.filter(title=pub_data['title']).first()
            if existing:
                return False
            
            # Create publication
            publication = Publication.objects.create(
                title=pub_data['title'],
                link=pub_data['link'],
                abstract=pub_data['abstract'],
                published_date=pub_data['published_date']
            )
            
            # Create/get authors and add to publication
            for author_data in pub_data['authors']:
                author, _ = Author.objects.get_or_create(
                    name=author_data['name'],
                    defaults={'profile_url': author_data['url']}
                )
                publication.authors.add(author)
            
            logger.info(f"Saved publication: {pub_data['title'][:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error saving publication: {e}")
            return False
