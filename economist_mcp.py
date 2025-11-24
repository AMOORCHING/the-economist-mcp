from fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
import os

# Initialize the MCP Server
mcp = FastMCP("The Economist Agent")

# Configuration
BASE_URL = "https://www.economist.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    # You must grab the 'cookie' header from your browser when logged into The Economist
    "Cookie": os.getenv("ECONOMIST_COOKIE") 
}

@mcp.tool()
def get_latest_briefing() -> str:
    """
    Fetches the latest 'The World in Brief' summary.
    Returns the full text of the briefing, including intro and mini-articles.
    """
    response = requests.get(f"{BASE_URL}/the-world-in-brief", headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Scope to the article container
    article = soup.select_one('article[data-testid="Article"]')
    container = article if article else soup
    
    content_parts = []
    
    # Select all relevant elements in order of appearance
    # 1. Intro paragraphs (data-component="the-world-in-brief-paragraph")
    # 2. Mini-article titles (class="css-p09rkj e1pqka930")
    # 3. Mini-article paragraphs (data-component="paragraph")
    
    selector = 'p[data-component="the-world-in-brief-paragraph"], .css-p09rkj.e1pqka930, p[data-component="paragraph"]'
    elements = container.select(selector)
    
    if not elements:
        return "Error: Could not find briefing content. Check cookie validity or paywall status."

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
        return "Error: Briefing content too short. Check cookie validity."
        
    return full_text

@mcp.tool()
def read_full_article(url: str) -> str:
    """
    Fetches the full text of a specific Economist article URL.
    Use this when the user asks to 'read' a specific headline.
    Returns the article title, subheading (if present), and full body text.
    """
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Scope to the article container
    article = soup.select_one('article[data-testid="Article"]')
    if not article:
        return "Error: Could not find article container. Check URL or cookie validity."
    
    # Extract title
    title_elem = article.select_one('.css-1tik00t.e1qjd5lc0')
    title = title_elem.get_text(strip=True) if title_elem else "Title not found"
    
    # Extract subheading (if present)
    subheading_elem = article.select_one('.css-1fxcbca.e6h2z500')
    subheading = subheading_elem.get_text(strip=True) if subheading_elem else None
    
    # Extract paragraphs using data-component attribute (more stable than CSS classes)
    paragraphs = []
    for p in article.select('p[data-component="paragraph"]'):
        # Get text while preserving structure (removes tags but keeps text)
        text = p.get_text(separator=' ', strip=True)
        if text:  # Only add non-empty paragraphs
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

if __name__ == "__main__":
    mcp.run()