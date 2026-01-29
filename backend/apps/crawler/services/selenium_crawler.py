"""
Selenium-based Web Crawler

BFS crawler for Coventry University publications using Selenium WebDriver.
This crawler can bypass Cloudflare protection by using a real browser.

Adapted from the previous project implementation.
"""

import os
import time
import logging
import re
import json
import unicodedata
from math import ceil
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils import timezone

from apps.search.models import Author, Publication

logger = logging.getLogger(__name__)


# =========================== Configuration ===========================
PORTAL_ROOT = "https://pureportal.coventry.ac.uk"
PERSONS_PREFIX = "/en/persons/"
BASE_URL = f"{PORTAL_ROOT}/en/organisations/ics-research-centre-for-computational-science-and-mathematical-mo/publications/"

# Crawl delay in seconds (politeness)
CRAWL_DELAY = 1.0
USER_AGENT = "CoventryPublicationCrawler/1.0 (Educational Research Project)"


# =========================== Robots.txt Compliance ===========================
class RobotsTxtChecker:
    """
    Handles robots.txt compliance for polite crawling.

    Note: Uses custom pattern matching because Python's RobotFileParser has bugs
    with wildcard patterns (it uses fnmatch where '?' is a wildcard, but in
    robots.txt standard RFC 9309, '?' is a literal character).
    """

    def __init__(self, base_url: str, user_agent: str = USER_AGENT):
        self.base_url = base_url
        self.user_agent = user_agent
        self.crawl_delay = CRAWL_DELAY
        self._loaded = False
        self._disallow_patterns: List[re.Pattern] = []
        self._allow_patterns: List[re.Pattern] = []

    def _robots_pattern_to_regex(self, pattern: str) -> re.Pattern:
        """
        Convert robots.txt pattern to regex.
        In robots.txt (RFC 9309):
        - '*' matches any sequence of characters
        - '$' at the end means end-of-string
        - '?' is a literal question mark (NOT a wildcard like in fnmatch!)
        """
        # Escape all regex metacharacters except * and $
        escaped = ""
        i = 0
        while i < len(pattern):
            ch = pattern[i]
            if ch == '*':
                escaped += '.*'
            elif ch == '$' and i == len(pattern) - 1:
                escaped += '$'
            elif ch in r'\^$.+?{}[]|()':
                escaped += '\\' + ch
            else:
                escaped += ch
            i += 1

        return re.compile(escaped)

    def load(self):
        """Load and parse robots.txt from the target site"""
        if self._loaded:
            return

        try:
            parsed = urlparse(self.base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            logger.info(f"Loading robots.txt from {robots_url}")

            import urllib.request
            req = urllib.request.Request(robots_url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')

            # Parse robots.txt manually for correct pattern matching
            current_user_agent = None
            applies_to_us = False

            for line in content.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Split on first colon
                if ':' not in line:
                    continue

                directive, value = line.split(':', 1)
                directive = directive.strip().lower()
                value = value.strip()

                if directive == 'user-agent':
                    current_user_agent = value
                    # Check if this applies to us (* matches all)
                    applies_to_us = (value == '*' or
                                    value.lower() in self.user_agent.lower() or
                                    self.user_agent.lower() in value.lower())
                elif applies_to_us:
                    if directive == 'disallow' and value:
                        pattern = self._robots_pattern_to_regex(value)
                        self._disallow_patterns.append(pattern)
                        logger.debug(f"Added disallow pattern: {value}")
                    elif directive == 'allow' and value:
                        pattern = self._robots_pattern_to_regex(value)
                        self._allow_patterns.append(pattern)
                        logger.debug(f"Added allow pattern: {value}")
                    elif directive == 'crawl-delay':
                        try:
                            delay = float(value)
                            self.crawl_delay = max(delay, CRAWL_DELAY)
                            logger.info(f"Using crawl delay from robots.txt: {self.crawl_delay}s")
                        except ValueError:
                            pass

            self._loaded = True
            logger.info(f"robots.txt loaded successfully ({len(self._disallow_patterns)} disallow rules)")

        except Exception as e:
            logger.warning(f"Could not load robots.txt: {e}. Using default settings.")
            self._loaded = True

    def can_fetch(self, url: str) -> bool:
        """Check if the URL can be fetched according to robots.txt"""
        if not self._loaded:
            self.load()

        try:
            parsed = urlparse(url)
            path = parsed.path
            if parsed.query:
                path = f"{path}?{parsed.query}"

            # Check allow patterns first (they take precedence)
            for pattern in self._allow_patterns:
                if pattern.match(path):
                    return True

            # Check disallow patterns
            for pattern in self._disallow_patterns:
                if pattern.match(path):
                    logger.debug(f"URL blocked by pattern: {pattern.pattern}")
                    return False

            # Default: allowed
            return True

        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True

    def get_crawl_delay(self) -> float:
        """Get the appropriate crawl delay"""
        if not self._loaded:
            self.load()
        return self.crawl_delay

    def wait(self):
        """Wait for the appropriate crawl delay"""
        delay = self.get_crawl_delay()
        if delay > 0:
            time.sleep(delay)


# Global robots.txt checker
_robots_checker = None


def get_robots_checker() -> RobotsTxtChecker:
    """Get or create the robots.txt checker"""
    global _robots_checker
    if _robots_checker is None:
        _robots_checker = RobotsTxtChecker(PORTAL_ROOT, USER_AGENT)
        _robots_checker.load()
    return _robots_checker


def reset_robots_checker():
    """Reset the global robots.txt checker (useful for testing or re-crawling)"""
    global _robots_checker
    _robots_checker = None


# =========================== Chrome Helpers ===========================
# Persistent browser profile directory for storing cookies (helps with Cloudflare)
# Use a simple path in user's home directory to avoid issues with spaces
BROWSER_PROFILE_DIR = os.path.expanduser("~/.coventry_crawler_profile")


def build_chrome_options(headless: bool = True, use_profile: bool = True):
    """Build Chrome options with anti-detection settings"""
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    # Use Brave binary if provided (Brave is Chromium-based)
    brave_binary = os.getenv("CRAWLER_BRAVE_BINARY")
    if brave_binary:
        opts.binary_location = brave_binary

    # Use persistent profile to maintain Cloudflare cookies
    if use_profile and not headless:
        os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)
        opts.add_argument(f"--user-data-dir={BROWSER_PROFILE_DIR}")
        logger.info(f"Using persistent browser profile: {BROWSER_PROFILE_DIR}")

    opts.add_argument("--window-size=1366,900")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--lang=en-US")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-popup-blocking")
    opts.add_argument("--disable-renderer-backgrounding")
    opts.add_argument("--disable-backgrounding-occluded-windows")
    opts.add_argument("--disable-features=CalculateNativeWinOcclusion,MojoVideoDecoder")
    opts.add_argument("--disable-plugins")
    opts.add_argument("--disable-background-networking")
    opts.add_argument("--memory-pressure-off")
    opts.page_load_strategy = "eager"

    # Preferences for speed
    prefs = {
        "profile.default_content_setting_values": {
            "plugins": 2,
            "popups": 2,
            "geolocation": 2,
            "notifications": 2,
            "media_stream": 2,
        }
    }
    opts.add_experimental_option("prefs", prefs)

    # Anti-detection settings
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    )
    return opts


def make_driver(headless: bool = True, use_profile: bool = True):
    """
    Create a WebDriver with anti-detection settings.

    Uses undetected-chromedriver to bypass Cloudflare bot detection.
    Falls back to regular Selenium if undetected-chromedriver fails.
    """
    try:
        import undetected_chromedriver as uc

        # Configure undetected-chromedriver options
        options = uc.ChromeOptions()

        if headless:
            options.add_argument("--headless=new")

        # Use Brave binary if provided
        brave_binary = os.getenv("CRAWLER_BRAVE_BINARY")
        if brave_binary:
            options.binary_location = brave_binary

        # Use persistent profile for cookies
        if use_profile and not headless:
            os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)
            options.add_argument(f"--user-data-dir={BROWSER_PROFILE_DIR}")
            logger.info(f"Using persistent browser profile: {BROWSER_PROFILE_DIR}")

        options.add_argument("--window-size=1366,900")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=en-US")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.page_load_strategy = "eager"

        logger.info("Creating undetected-chromedriver (Cloudflare bypass enabled)")

        # Specify browser version to avoid mismatch (Brave 143.x based on Chromium 143)
        driver = uc.Chrome(options=options, headless=headless, version_main=143)
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(0.5)

        return driver

    except Exception as e:
        logger.warning(f"undetected-chromedriver failed: {e}. Falling back to regular Selenium.")

        # Fallback to regular Selenium
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService

        service = ChromeService(log_output=os.devnull)
        driver = webdriver.Chrome(service=service, options=build_chrome_options(headless, use_profile))
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(0.5)

        # Remove webdriver flag
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
            )
        except Exception:
            pass

        return driver


def accept_cookies_if_present(driver):
    """Accept cookies dialog if present"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    
    try:
        btn = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.1)
    except TimeoutException:
        pass
    except Exception:
        pass


# =========================== Utilities ===========================
FIRST_DIGIT = re.compile(r"\d")
NAME_PAIR = re.compile(
    r"[A-Z][A-Za-z''\-]+,\s*(?:[A-Z](?:\.)?)(?:\s*[A-Z](?:\.)?)*", flags=re.UNICODE
)
SPACE = re.compile(r"\s+")


def _uniq_str(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for x in seq:
        x = x.strip()
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _uniq_authors(objs: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    seen: set[Tuple[str, str]] = set()
    out: List[Dict[str, Optional[str]]] = []
    for o in objs:
        name = (o.get("name") or "").strip()
        profile = (o.get("profile") or "").strip()
        key = (name, profile)
        if name and key not in seen:
            seen.add(key)
            out.append({"name": name, "profile": profile or None})
    return out


def _is_person_profile_url(href: str) -> bool:
    """Accept only /en/persons/<slug>"""
    if not href:
        return False
    try:
        u = urlparse(href)
    except Exception:
        return False
    if u.netloc and "coventry.ac.uk" not in u.netloc:
        return False
    path = (u.path or "").rstrip("/")
    if not path.startswith(PERSONS_PREFIX):
        return False
    slug = path[len(PERSONS_PREFIX):].strip("/")
    if not slug or slug.startswith("?"):
        return False
    return True


def _looks_like_person_name(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    bad = {"profiles", "persons", "people", "overview"}
    if t.lower() in bad:
        return False
    return ((" " in t) or ("," in t)) and sum(ch.isalpha() for ch in t) >= 4


# =========================== Listing Page Scraper ===========================
def wait_for_cloudflare(driver, timeout: int = 30, is_first_page: bool = False):
    """
    Wait for Cloudflare challenge to clear.

    If running in non-headless mode on the first page, this gives the user time
    to manually solve the challenge if needed.
    """
    from selenium.webdriver.common.by import By

    start_time = time.time()
    challenge_detected = False

    while time.time() - start_time < timeout:
        page_source = driver.page_source
        title = driver.title

        # Check if Cloudflare challenge is present
        is_cloudflare = (
            'Just a moment' in page_source or
            'Cloudflare' in title or
            'cf-browser-verification' in page_source or
            'challenge-running' in page_source
        )

        if is_cloudflare:
            if not challenge_detected:
                challenge_detected = True
                if is_first_page:
                    logger.info("Cloudflare challenge detected. If running with --no-headless, please solve the challenge in the browser window...")
                else:
                    logger.info("Waiting for Cloudflare challenge to clear...")
            time.sleep(2)
        else:
            # Page loaded successfully
            if challenge_detected:
                logger.info("Cloudflare challenge cleared successfully!")
            return True

    logger.warning(f"Cloudflare did not clear after {timeout}s")
    return False


def scrape_listing_page(driver, page_idx: int, cloudflare_wait: int = 15, is_first_page: bool = False) -> List[Dict]:
    """Scrape a single listing page for publication links"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import TimeoutException

    url = f"{BASE_URL}?page={page_idx}"

    # Check robots.txt compliance
    robots = get_robots_checker()
    if not robots.can_fetch(url):
        logger.warning(f"URL disallowed by robots.txt: {url}")
        return []

    # Apply polite crawl delay
    robots.wait()

    driver.get(url)

    # Wait for Cloudflare to clear
    wait_for_cloudflare(driver, cloudflare_wait, is_first_page=is_first_page)

    accept_cookies_if_present(driver)
    
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, ".result-container h3.title a")
            or "No results" in d.page_source
        )
    except TimeoutException:
        # Give it more time
        time.sleep(5)

    rows = []
    for c in driver.find_elements(By.CLASS_NAME, "result-container"):
        try:
            a = c.find_element(By.CSS_SELECTOR, "h3.title a")
            title = a.text.strip()
            link = a.get_attribute("href")
            if title and link:
                rows.append({"title": title, "link": link})
        except Exception:
            continue
    return rows


def scrape_single_listing_page(page_idx: int, headless: bool = True) -> List[Dict]:
    """Single page scraper for parallel execution"""
    driver = make_driver(headless)
    try:
        return scrape_listing_page(driver, page_idx)
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def gather_all_listing_links_sequential(
    max_pages: Optional[int],
    headless: bool = False,
    max_empty_pages: int = 2
) -> Tuple[List[Dict], int]:
    """
    Collect all publication links using a SINGLE browser session.
    Use this mode when Cloudflare protection is active - the browser session
    persists and Cloudflare only needs to be cleared once.
    """
    total_label = max_pages if max_pages and max_pages > 0 else "auto"
    logger.info(f"[STAGE 1] Collecting links from {total_label} pages (sequential mode)...")

    all_rows: List[Dict] = []
    driver = make_driver(headless)
    page_idx = 0
    empty_pages = 0
    pages_crawled = 0
    
    try:
        while True:
            if max_pages and max_pages > 0 and page_idx >= max_pages:
                break
            try:
                # First page gets longer Cloudflare wait (60s for manual solving)
                is_first = (page_idx == 0)
                cloudflare_wait = 60 if is_first else 5
                rows = scrape_listing_page(driver, page_idx, cloudflare_wait, is_first_page=is_first)
                if rows:
                    all_rows.extend(rows)
                    empty_pages = 0
                    logger.info(f"[LIST] Page {page_idx+1}/{total_label} -> {len(rows)} items")
                else:
                    empty_pages += 1
                    logger.info(f"[LIST] Page {page_idx+1}/{total_label} -> empty (may be end of results)")
            except Exception as e:
                empty_pages += 1
                logger.error(f"[LIST] Page {page_idx+1} failed: {e}")
            finally:
                pages_crawled += 1

            if page_idx == 0 and empty_pages > 0:
                break
            if empty_pages >= max_empty_pages:
                break

            page_idx += 1
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    # Remove duplicates by link
    uniq = {}
    for r in all_rows:
        uniq[r["link"]] = r
    return list(uniq.values()), pages_crawled


def gather_all_listing_links(
    max_pages: Optional[int],
    headless: bool = True,
    list_workers: int = 4
) -> Tuple[List[Dict], int]:
    """Collect all publication links from listing pages (parallelized)"""
    
    if not max_pages or max_pages <= 0:
        return gather_all_listing_links_sequential(max_pages, headless)

    # Use sequential mode for non-headless (Cloudflare requires single browser session)
    if not headless:
        return gather_all_listing_links_sequential(max_pages, headless)
    
    logger.info(f"[STAGE 1] Collecting links from {max_pages} pages with {list_workers} workers...")

    all_rows: List[Dict] = []

    with ThreadPoolExecutor(max_workers=list_workers) as executor:
        future_to_page = {
            executor.submit(scrape_single_listing_page, i, headless): i
            for i in range(max_pages)
        }

        for future in as_completed(future_to_page):
            page_idx = future_to_page[future]
            try:
                rows = future.result()
                if rows:
                    all_rows.extend(rows)
                    logger.info(f"[LIST] Page {page_idx+1}/{max_pages} → {len(rows)} items")
                else:
                    logger.info(f"[LIST] Page {page_idx+1}/{max_pages} → empty")
            except Exception as e:
                logger.error(f"[LIST] Page {page_idx+1} failed: {e}")

    # Remove duplicates by link
    uniq = {}
    for r in all_rows:
        uniq[r["link"]] = r
    return list(uniq.values()), len(future_to_page)


# =========================== Detail Page Scraper ===========================
def _authors_from_header_anchors(driver) -> List[Dict]:
    """Grab author links from the header section"""
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import NoSuchElementException
    
    # Find Y threshold of tab bar
    tabs_y = None
    for xp in [
        "//a[normalize-space()='Overview']",
        "//nav[contains(@class,'tabbed-navigation')]",
        "//div[contains(@class,'navigation') and .//a[contains(.,'Overview')]]",
    ]:
        try:
            el = driver.find_element(By.XPATH, xp)
            tabs_y = el.location.get("y", None)
            if tabs_y:
                break
        except Exception:
            continue
    if tabs_y is None:
        tabs_y = 900

    candidates: List[Dict[str, Optional[str]]] = []
    seen = set()
    for a in driver.find_elements(By.CSS_SELECTOR, "a[href*='/en/persons/']"):
        try:
            y = a.location.get("y", 99999)
            if y >= tabs_y:
                continue
            href = (a.get_attribute("href") or "").strip()
            if not _is_person_profile_url(href):
                continue
            try:
                name = a.find_element(By.CSS_SELECTOR, "span").text.strip()
            except NoSuchElementException:
                name = (a.text or "").strip()
            if not _looks_like_person_name(name):
                continue
            key = (name, href)
            if key in seen:
                continue
            seen.add(key)
            candidates.append({"name": name, "profile": urljoin(driver.current_url, href)})
        except Exception:
            continue

    return _uniq_authors(candidates)


def extract_detail_for_link(driver, link: str, title_hint: str) -> Dict:
    """Extract detailed information from a publication page"""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    
    # Check robots.txt compliance
    robots = get_robots_checker()
    if not robots.can_fetch(link):
        logger.warning(f"URL disallowed by robots.txt: {link}")
        return {
            "title": title_hint or "",
            "link": link,
            "authors": [],
            "published_date": None,
            "abstract": "",
        }

    # Apply polite crawl delay
    robots.wait()

    driver.get(link)

    # Accept cookies if present
    try:
        btn = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        driver.execute_script("arguments[0].click();", btn)
    except:
        pass

    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
        )
    except TimeoutException:
        time.sleep(1)

    # Extract title
    try:
        title = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
    except NoSuchElementException:
        title = title_hint or ""

    # Click "show more" buttons
    try:
        for b in driver.find_elements(
            By.XPATH,
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'show') or "
            "contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'more')]",
        )[:2]:
            try:
                b.click()
                time.sleep(0.1)
            except:
                continue
    except:
        pass

    # Extract authors
    author_objs: List[Dict[str, Optional[str]]] = []
    try:
        author_objs = _authors_from_header_anchors(driver)
        author_objs = [
            a for a in author_objs
            if _looks_like_person_name(a.get("name", ""))
            and _is_person_profile_url(a.get("profile", ""))
        ]
    except:
        pass

    # Extract date
    published_date = None
    for sel in ["span.date", "time[datetime]", "time"]:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            published_date = el.get_attribute("datetime") or el.text.strip()
            if published_date:
                break
        except:
            continue

    # Extract abstract
    abstract_txt = ""
    abstract_selectors = [
        "section#abstract .textblock",
        "section.abstract .textblock",
        "div.abstract .textblock",
        "div#abstract .textblock",
        "section#abstract",
        "div#abstract",
        "[data-section='abstract'] .textblock",
        ".abstract .textblock",
        ".abstract p",
        ".abstract div",
        "div.textblock",
    ]

    for sel in abstract_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in elements:
                txt = el.text.strip()
                if len(txt) > 30:
                    abstract_txt = txt
                    break
            if abstract_txt:
                break
        except:
            continue

    # Fallback: try meta description
    if not abstract_txt:
        try:
            meta_selectors = [
                'meta[name="description"]',
                'meta[name="abstract"]',
                'meta[property="og:description"]',
                'meta[name="citation_abstract"]',
            ]
            for sel in meta_selectors:
                try:
                    meta = driver.find_element(By.CSS_SELECTOR, sel)
                    content = meta.get_attribute("content")
                    if content and len(content.strip()) > 30:
                        abstract_txt = content.strip()
                        break
                except:
                    continue
        except:
            pass

    return {
        "title": title,
        "link": link,
        "authors": _uniq_authors(author_objs),
        "published_date": published_date,
        "abstract": abstract_txt,
    }


# =========================== Worker Functions ===========================
def worker_detail_batch(batch: List[Dict], headless: bool = True) -> List[Dict]:
    """Process a batch of publication links"""
    # Don't use profile for parallel workers to avoid conflicts
    driver = make_driver(headless=headless, use_profile=False)
    out: List[Dict] = []
    try:
        for i, it in enumerate(batch, 1):
            try:
                rec = extract_detail_for_link(driver, it["link"], it.get("title", ""))
                out.append(rec)
                if i % 2 == 0:
                    logger.info(f"[WORKER] {i}/{len(batch)} parsed")
            except Exception as e:
                logger.error(f"[WORKER] ERR {it['link']}: {str(e)[:100]}")
                out.append({
                    "title": it.get("title", ""),
                    "link": it["link"],
                    "authors": [],
                    "published_date": None,
                    "abstract": "",
                })
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    return out


def chunk(items: List[Dict], n: int) -> List[List[Dict]]:
    """Split items into chunks for parallel processing"""
    if n <= 1:
        return [items]
    size = max(3, ceil(len(items) / (n * 2)))
    return [items[i:i + size] for i in range(0, len(items), size)]


# =========================== Main Crawler Class ===========================
class SeleniumPublicationCrawler:
    """
    Selenium-based BFS crawler for Coventry University publications.
    Can bypass Cloudflare protection by using a real browser.
    """

    def __init__(
        self,
        max_pages: Optional[int] = None,
        headless: bool = True,
        list_workers: int = 4,
        detail_workers: int = 2  # Reduced to avoid issues with concurrent browser instances
    ):
        self.max_pages = max_pages
        self.headless = headless
        self.list_workers = list_workers
        self.detail_workers = detail_workers

    def crawl(self) -> Dict:
        """
        Perform BFS crawl of publications using Selenium.

        Returns:
            Dictionary with crawl statistics
        """
        # Reset robots.txt checker to ensure fresh data
        reset_robots_checker()

        max_label = self.max_pages if self.max_pages and self.max_pages > 0 else "auto"
        logger.info(f"Starting Selenium BFS crawl (max {max_label} pages)")
        start_time = time.time()

        # Stage 1: Collect listing links
        logger.info("[STAGE 1] Collecting publication links...")
        listing, pages_crawled = gather_all_listing_links(
            self.max_pages,
            headless=self.headless,
            list_workers=self.list_workers
        )
        stage1_time = time.time() - start_time
        logger.info(f"[STAGE 1] Collected {len(listing)} unique links in {stage1_time:.1f}s")

        if not listing:
            logger.warning("No publications found on listing pages.")
            return {
                'pages_crawled': pages_crawled,
                'new_publications': 0,
                'total_urls_visited': 0,
                'duration_seconds': stage1_time
            }

        # Stage 2: Extract details
        logger.info(f"[STAGE 2] Scraping details with {self.detail_workers} workers...")
        stage2_start = time.time()
        
        batches = chunk(listing, max(1, self.detail_workers))
        results: List[Dict] = []
        
        with ThreadPoolExecutor(max_workers=max(1, self.detail_workers)) as ex:
            futs = [ex.submit(worker_detail_batch, batch, self.headless) for batch in batches]
            for fut in as_completed(futs):
                part = fut.result() or []
                results.extend(part)
                logger.info(f"[STAGE 2] Completed batch (+{len(part)} items)")

        stage2_time = time.time() - stage2_start

        # Merge results (prefer detail results)
        by_link: Dict[str, Dict] = {}
        for it in listing:
            by_link[it["link"]] = {"title": it["title"], "link": it["link"]}
        for rec in results:
            by_link[rec["link"]] = rec

        final_rows = list(by_link.values())

        # Save to database
        new_publications = 0
        for pub_data in final_rows:
            if self._save_publication(pub_data):
                new_publications += 1

        total_time = time.time() - start_time

        result = {
            'pages_crawled': pages_crawled,
            'publications_found': len(final_rows),
            'new_publications': new_publications,
            'stage1_time': stage1_time,
            'stage2_time': stage2_time,
            'duration_seconds': total_time
        }

        # Export all publications to JSON file
        self._export_to_json()

        logger.info(f"Crawl complete: {result}")
        return result

    def _save_publication(self, pub_data: Dict) -> bool:
        """Save a publication to the database."""
        try:
            # Check if publication already exists
            existing = Publication.objects.filter(title=pub_data['title']).first()
            if existing:
                return False

            # Create publication
            publication = Publication.objects.create(
                title=pub_data['title'],
                link=pub_data['link'],
                abstract=pub_data.get('abstract', ''),
                published_date=pub_data.get('published_date', '')
            )

            # Create/get authors and add to publication
            for author_data in pub_data.get('authors', []):
                author, _ = Author.objects.get_or_create(
                    name=author_data['name'],
                    defaults={'profile_url': author_data.get('profile', '')}
                )
                publication.authors.add(author)

            logger.info(f"Saved publication: {pub_data['title'][:50]}...")
            return True

        except Exception as e:
            logger.error(f"Error saving publication: {e}")
            return False

    def _export_to_json(self, file_path: str = None):
        """Export all publications from database to JSON file."""
        if file_path is None:
            # Default path: project_root/data/publications.json
            # From: backend/apps/crawler/services/selenium_crawler.py
            # Go up: services -> crawler -> apps -> backend -> project_root
            file_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
                "data", "publications.json"
            )

        publications = Publication.objects.prefetch_related('authors').all()

        data = {
            "publications": [
                {
                    "title": pub.title,
                    "link": pub.link,
                    "abstract": pub.abstract,
                    "published_date": pub.published_date,
                    "authors": [
                        {
                            "name": author.name,
                            "profile_url": author.profile_url or ""
                        }
                        for author in pub.authors.all()
                    ]
                }
                for pub in publications
            ]
        }

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(data['publications'])} publications to {file_path}")
