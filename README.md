# AI Tools Directory

An auto-updating directory of 100+ AI tools, with 5 new tools added every night at midnight UTC.

## How It Works

1. **GitHub Actions** runs nightly at midnight UTC
2. **Scraper** fetches new AI tools from GitHub Trending, Product Hunt, and other sources
3. **Auto-commit** pushes updates to the repository
4. **Cloudflare Pages** auto-deploys the updated site

## Files

- `tools-database.json` - Master database of all AI tools
- `update_tools.py` - Scraper script that adds 5 new tools daily
- `.github/workflows/update-tools.yml` - GitHub Actions workflow
- `update_log.jsonl` - Log of all updates

## Data Structure

```json
{
  "metadata": {
    "version": "1.0.0",
    "last_updated": "2026-03-31T00:00:00Z",
    "total_tools": 100,
    "categories": ["Text & Writing", "Image & Art", ...]
  },
  "tools": [
    {
      "id": "tool-001",
      "name": "ChatGPT",
      "description": "...",
      "category": "Chatbots & Assistants",
      "url": "https://chat.openai.com",
      "pricing": "Freemium",
      "date_added": "2026-03-31",
      "is_new": true,
      "featured": true
    }
  ]
}
```

## Categories

- Text & Writing
- Image & Art
- Code & Development
- Audio & Voice
- Video & Animation
- Data & Analytics
- Chatbots & Assistants
- Automation & Productivity
- Search & Research
- Marketing & SEO

## License

© 2026 Mankato Web Solutions
