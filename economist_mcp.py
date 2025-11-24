from fastmcp import FastMCP
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Initialize the MCP Server
mcp = FastMCP("The Economist Agent")
load_dotenv()

# Configuration
BASE_URL = "https://www.economist.com"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_content(url: str) -> str:
    """
    Fetches content using Playwright to bypass Cloudflare.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={'width': 1280, 'height': 800}
        )
        
        # Add cookie if available
        cookie_str = os.getenv("ECONOMIST_COOKIE")
        if cookie_str:
            domain = ".economist.com"
            cookies = []
            for item in cookie_str.split(';'):
                if '=' in item:
                    try:
                        name, value = item.strip().split('=', 1)
                        cookies.append({
                            "name": name,
                            "value": value,
                            "domain": domain,
                            "path": "/"
                        })
                    except ValueError:
                        continue
            if cookies:
                context.add_cookies(cookies)

        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for Cloudflare challenge to resolve or content to appear
            try:
                # Wait for main article content or footer, timeout after 30s
                page.wait_for_selector("article, footer, [data-testid='Article']", timeout=30000)
            except:
                pass # Proceed anyway
            
            # Sometimes scrolling down triggers lazy loading or helps pass bot checks
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000) # Small delay
            
            content = page.content()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            content = ""
        finally:
            browser.close()
            
    return content

def _get_latest_briefing_logic() -> str:
    """
    Internal logic for fetching the briefing.
    """
    url = f"{BASE_URL}/the-world-in-brief"
    html_content = fetch_content(url)
    
    if not html_content:
        return "Error: Failed to fetch content. Cloudflare might be blocking or network issue."

    soup = BeautifulSoup(html_content, "html.parser")
    
    # Scope to the article container
    article = soup.select_one('article[data-testid="Article"]')
    container = article if article else soup
    
    content_parts = []
    
    # Select all relevant elements in order of appearance
    selector = 'p[data-component="the-world-in-brief-paragraph"], .css-p09rkj.e1pqka930, p[data-component="paragraph"]'
    elements = container.select(selector)
    
    if not elements:
        # Check for Cloudflare specific text
        text = soup.get_text()
        if "Just a moment" in text or "Enable JavaScript" in text:
             return "Error: Still blocked by Cloudflare challenge. Please try updating cookies."
        return "Error: Could not find briefing content. Structure might have changed."

    for elem in elements:
        text = elem.get_text(separator=' ', strip=True)
        if not text:
            continue
            
        # Identify element type based on attributes/classes
        if elem.name == 'p' and elem.get('data-component') == 'the-world-in-brief-paragraph':
            content_parts.append(text)
        elif 'css-p09rkj' in elem.get('class', []): # Title
             content_parts.append(f"\n## {text}")
        elif elem.name == 'p' and elem.get('data-component') == 'paragraph':
            content_parts.append(text)
            
    full_text = "\n\n".join(content_parts)
    
    if len(full_text) < 100:
        return "Error: Briefing content too short."
        
    return full_text

def _read_full_article_logic(url: str) -> str:
    """
    Internal logic for reading an article.
    """
    html_content = fetch_content(url)
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Scope to the article container
    article = soup.select_one('article[data-testid="Article"]')
    if not article:
        if "Just a moment" in soup.get_text():
             return "Error: Blocked by Cloudflare challenge."
        return "Error: Could not find article container. Check URL or cookie validity."
    
    # Extract title
    title_elem = article.select_one('.css-1tik00t.e1qjd5lc0')
    title = title_elem.get_text(strip=True) if title_elem else "Title not found"
    
    # Extract subheading (if present)
    subheading_elem = article.select_one('.css-1fxcbca.e6h2z500')
    subheading = subheading_elem.get_text(strip=True) if subheading_elem else None
    
    # Extract paragraphs using data-component attribute
    paragraphs = []
    for p in article.select('p[data-component="paragraph"]'):
        text = p.get_text(separator=' ', strip=True)
        if text:
            paragraphs.append(text)
    
    # Build the full article text
    article_parts = [f"Title: {title}"]
    
    if subheading:
        article_parts.append(f"Subheading: {subheading}")
    
    article_parts.append("\nBody:\n" + "\n\n".join(paragraphs))
    
    full_text = "\n".join(article_parts)
    
    if len(paragraphs) == 0 or len(full_text) < 100:
        return "Error: Could not extract sufficient text. Check cookie validity or paywall status."
        
    return full_text

@mcp.tool()
def get_latest_briefing() -> str:
    """
    Fetches the latest 'The World in Brief' summary.
    Returns the full text of the briefing, including intro and mini-articles.
    """
    return _get_latest_briefing_logic()

@mcp.tool()
def read_full_article(url: str) -> str:
    """
    Fetches the full text of a specific Economist article URL.
    Use this when the user asks to 'read' a specific headline.
    Returns the article title, subheading (if present), and full body text.
    """
    return _read_full_article_logic(url)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Testing get_latest_briefing()...")
        try:
            print(_get_latest_briefing_logic())
        except Exception as e:
            print(f"Test failed: {e}")
    else:
        mcp.run()
