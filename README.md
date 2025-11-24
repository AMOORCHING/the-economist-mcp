# The Economist Poke MCP

An MCP (Model Context Protocol) server that fetches content from The Economist.

## Features

- **Latest Briefing**: Fetch "The World in Brief" daily summary from The Economist
- **Full Articles**: Read complete articles from The Economist by URL
- **Cloudflare Bypass**: Uses Playwright to handle Cloudflare protection
- **MCP Integration**: Exposes tools via the Model Context Protocol for use with AI assistants

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd the-economist-poke-mcp
```

2. Install dependencies using `uv` (recommended) or `pip`:
```bash
# Using uv
uv sync

# Or using pip
pip install -e .
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

## Configuration

Create a `.env` file in the project root with your Economist cookie:

```env
ECONOMIST_COOKIE=your_cookie_string_here
```

To get your cookie:
1. Log in to [economist.com](https://www.economist.com)
2. Open browser developer tools (cmd/ctrl + shift + i)
3. Go to Application/Storage → Cookies
4. Copy the relevant cookie values (you may need multiple cookies separated by semicolons)

**Note**: The cookie is used to bypass paywalls and access subscriber content. Make sure to keep it secure and don't commit it to version control.

## Usage

### Running the MCP Server

Start the MCP server:

```bash
python economist_mcp.py
```

Or if using the entry point:

```bash
python -m economist_mcp
```

### Testing

Test the briefing fetch functionality:

```bash
python economist_mcp.py test
```

### Available Tools

The MCP server exposes two tools:

#### `get_latest_briefing()`
Fetches the latest "The World in Brief" summary from The Economist. Returns the full text including intro and mini-articles.

#### `read_full_article(url: str)`
Fetches the full text of a specific Economist article. Requires the article URL as input. Returns the article title, subheading (if present), and full body text.

### Integration with Poke

This MCP is designed to work with [Poke by Interaction.co](https://interaction.co/poke). Configure Poke to use this MCP server to receive text message updates about important news from The Economist.

## Requirements

- Python >= 3.13
- Playwright (for browser automation)
- BeautifulSoup4 (for HTML parsing)
- FastMCP (MCP framework)
- python-dotenv (for environment variable management)

## How It Works

1. **Content Fetching**: Uses Playwright with Chromium to fetch web pages, bypassing Cloudflare protection
2. **HTML Parsing**: BeautifulSoup extracts structured content from The Economist's HTML
3. **MCP Tools**: FastMCP exposes the functionality as MCP tools that can be called by AI assistants
4. **Cookie Authentication**: Uses stored cookies to access subscriber-only content

## Troubleshooting

### Cloudflare Blocking
If you see "Just a moment" or "Enable JavaScript" errors:
- Update your `ECONOMIST_COOKIE` in the `.env` file
- Ensure cookies are properly formatted (name=value pairs separated by semicolons)

### Content Not Found
If articles or briefings aren't being extracted:
- The Economist's HTML structure may have changed
- Check that your cookie is valid and not expired
- Verify you have an active subscription

## License

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
