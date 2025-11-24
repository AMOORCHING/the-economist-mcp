from mcp.server.fastmcp import FastMCP
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
    Fetches the list of articles from 'The World in Brief' or the homepage.
    Returns a formatted string of headlines and URLs.
    """
    response = requests.get(f"{BASE_URL}/the-world-in-brief", headers=HEADERS)
    soup = BeautifulSoup(response.content, "html.parser")
    
    articles = []

    for item in soup.select("h3 a"): 
        title = item.get_text().strip()
        link = item['href']
        if not link.startswith("http"):
            link = BASE_URL + link
        articles.append(f"- {title}: {link}")
    
    return "\n".join(articles[:10])

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