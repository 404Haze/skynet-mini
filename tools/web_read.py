"""
Web page reader for skynet-mini.

Fetches a URL and extracts clean readable text content.
Uses requests + html2text-style extraction, or falls back to plain text.
"""

import re
import urllib.request
import urllib.error


def _extract_text(html: str) -> str:
    """Crude but effective HTML-to-text extraction without dependencies."""
    # Remove scripts and styles
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove head section
    html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Replace block elements with newlines
    html = re.sub(r'</?(div|p|h[1-6]|li|tr|br|article|section|header|footer|nav|main)[^>]*>', '\n', html, flags=re.IGNORECASE)
    # Remove remaining tags
    html = re.sub(r'<[^>]+>', '', html)
    # Decode entities
    html = html.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    html = html.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    # Collapse whitespace
    lines = [line.strip() for line in html.split('\n')]
    lines = [line for line in lines if line]
    return '\n'.join(lines)


def web_read(url: str, max_chars: int = 3000) -> dict:
    """
    Fetch a web page and extract its readable text content.

    Args:
        url: The URL of the page to read.
        max_chars: Maximum characters to return (default 3000).

    Returns:
        A dict with 'status' and either 'content' (extracted text)
        or 'error_message' on failure.
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'skynet-mini/1.0 (terminal AI agent)',
                'Accept': 'text/html,text/plain',
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            raw = response.read()

            # Try to decode
            charset = 'utf-8'
            if 'charset=' in content_type:
                charset = content_type.split('charset=')[-1].split(';')[0].strip()

            try:
                text = raw.decode(charset)
            except (UnicodeDecodeError, LookupError):
                text = raw.decode('utf-8', errors='replace')

        # If it's HTML, extract text
        if 'text/html' in content_type or text.strip().startswith('<!DOCTYPE') or '<html' in text[:200].lower():
            text = _extract_text(text)

        # Truncate if needed
        if len(text) > max_chars:
            text = text[:max_chars] + '\n\n[... truncated, use a smaller max_chars or read specific sections ...]'

        if not text.strip():
            return {
                "status": "error",
                "error_message": "Page returned no readable content.",
            }

        return {
            "status": "success",
            "content": text.strip(),
            "url": url,
        }

    except urllib.error.HTTPError as e:
        return {
            "status": "error",
            "error_message": f"HTTP {e.code}: {e.reason}",
        }
    except urllib.error.URLError as e:
        return {
            "status": "error",
            "error_message": f"Could not reach {url}: {str(e.reason)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to read page: {str(e)}",
        }
