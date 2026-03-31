#!/usr/bin/env python3
"""
AI Tools Directory Auto-Updater
Scrapes AI tools from various sources and adds them to the database.
Runs nightly via GitHub Actions.
"""

import json
import os
import random
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# Configuration
DATABASE_FILE = "tools-database.json"
UPDATE_LOG_FILE = "update_log.jsonl"
TOOLS_TO_ADD_PER_RUN = 5
MAX_DAILY_SCRAPE_ATTEMPTS = 20

# Data sources to scrape
DATA_SOURCES = {
    "github_trending": "https://github.com/trending",
    "product_hunt": "https://www.producthunt.com/topics/artificial-intelligence",
    "alternativeto": "https://alternativeto.net/platform/artificial-intelligence/",
}

# Fallback: Known AI tools to add if scraping fails
FALLBACK_TOOLS = [
    {
        "name": "Stable Diffusion",
        "description": "Open-source image generation model with local and cloud options.",
        "category": "Image & Art",
        "url": "https://stability.ai",
        "pricing": "Freemium"
    },
    {
        "name": "Grammarly",
        "description": "AI-powered writing assistant for grammar and style improvements.",
        "category": "Text & Writing",
        "url": "https://www.grammarly.com",
        "pricing": "Freemium"
    },
    {
        "name": "Otter.ai",
        "description": "AI meeting assistant that records and transcribes conversations.",
        "category": "Audio & Voice",
        "url": "https://otter.ai",
        "pricing": "Freemium"
    },
    {
        "name": "Synthesia",
        "description": "Create AI videos with virtual presenters from text.",
        "category": "Video & Animation",
        "url": "https://www.synthesia.io",
        "pricing": "Paid"
    },
    {
        "name": "Hugging Face",
        "description": "Platform for sharing and deploying machine learning models.",
        "category": "Code & Development",
        "url": "https://huggingface.co",
        "pricing": "Freemium"
    },
    {
        "name": "Copy.ai",
        "description": "AI copywriting tool for marketing content and sales copy.",
        "category": "Marketing & SEO",
        "url": "https://www.copy.ai",
        "pricing": "Freemium"
    },
    {
        "name": "Descript",
        "description": "AI-powered audio/video editor with transcription and overdub.",
        "category": "Audio & Voice",
        "url": "https://www.descript.com",
        "pricing": "Freemium"
    },
    {
        "name": "Replicate",
        "description": "Run machine learning models in the cloud with one line of code.",
        "category": "Code & Development",
        "url": "https://replicate.com",
        "pricing": "Pay-per-use"
    },
    {
        "name": "Poe",
        "description": "Platform to chat with multiple AI models including GPT-4 and Claude.",
        "category": "Chatbots & Assistants",
        "url": "https://poe.com",
        "pricing": "Freemium"
    },
    {
        "name": "Canva AI",
        "description": "AI design tools integrated into Canva for images, presentations, and more.",
        "category": "Image & Art",
        "url": "https://www.canva.com/ai-image-generator",
        "pricing": "Freemium"
    },
    {
        "name": "Anthropic Console",
        "description": "Developer platform for building with Claude AI models.",
        "category": "Code & Development",
        "url": "https://console.anthropic.com",
        "pricing": "Pay-per-use"
    },
    {
        "name": "LangChain",
        "description": "Framework for building applications with large language models.",
        "category": "Code & Development",
        "url": "https://www.langchain.com",
        "pricing": "Open Source"
    },
    {
        "name": "Fireflies.ai",
        "description": "AI meeting notetaker that transcribes and summarizes calls.",
        "category": "Automation & Productivity",
        "url": "https://fireflies.ai",
        "pricing": "Freemium"
    },
    {
        "name": "Beautiful.ai",
        "description": "AI presentation maker that designs slides automatically.",
        "category": "Automation & Productivity",
        "url": "https://www.beautiful.ai",
        "pricing": "Paid"
    },
    {
        "name": "Lovo",
        "description": "AI voice generator with 500+ voices in 100+ languages.",
        "category": "Audio & Voice",
        "url": "https://lovo.ai",
        "pricing": "Paid"
    }
]


def load_database() -> Dict:
    """Load the tools database from JSON file."""
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "metadata": {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "total_tools": 0,
            "categories": [
                "Text & Writing",
                "Image & Art",
                "Code & Development",
                "Audio & Voice",
                "Video & Animation",
                "Data & Analytics",
                "Chatbots & Assistants",
                "Automation & Productivity",
                "Search & Research",
                "Marketing & SEO"
            ]
        },
        "tools": []
    }


def save_database(data: Dict) -> None:
    """Save the tools database to JSON file."""
    data["metadata"]["last_updated"] = datetime.now().isoformat()
    data["metadata"]["total_tools"] = len(data["tools"])
    
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def log_update(tools_added: int, source: str, details: str = "") -> None:
    """Log the update to a JSONL file."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tools_added": tools_added,
        "source": source,
        "details": details
    }
    with open(UPDATE_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')


def get_existing_tool_names(data: Dict) -> set:
    """Get set of existing tool names (lowercase) for deduplication."""
    return {tool["name"].lower() for tool in data["tools"]}


def generate_tool_id(data: Dict) -> str:
    """Generate a unique tool ID."""
    existing_ids = {tool["id"] for tool in data["tools"]}
    counter = len(data["tools"]) + 1
    while True:
        new_id = f"tool-{counter:03d}"
        if new_id not in existing_ids:
            return new_id
        counter += 1


def scrape_github_trending() -> List[Dict]:
    """Scrape trending AI repositories from GitHub."""
    tools = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(
            "https://github.com/trending/python?since=daily",
            headers=headers,
            timeout=30
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for AI/ML related repositories
        articles = soup.find_all('article', class_='Box-row')
        for article in articles[:5]:
            try:
                name_elem = article.find('h2', class_='h3')
                if name_elem:
                    name = name_elem.text.strip().replace('\n', '').replace(' ', '')
                    desc_elem = article.find('p', class_='col-9')
                    description = desc_elem.text.strip() if desc_elem else "AI/ML repository"
                    
                    # Only include if it looks AI-related
                    ai_keywords = ['ai', 'ml', 'machine learning', 'neural', 'gpt', 'llm', 'model']
                    if any(keyword in description.lower() for keyword in ai_keywords):
                        tools.append({
                            "name": name.split('/')[-1].replace('-', ' ').title(),
                            "description": description[:150] + "..." if len(description) > 150 else description,
                            "category": "Code & Development",
                            "url": f"https://github.com/{name}",
                            "pricing": "Open Source"
                        })
            except Exception:
                continue
    except Exception as e:
        print(f"GitHub scraping failed: {e}")
    
    return tools


def scrape_product_hunt() -> List[Dict]:
    """Scrape AI products from Product Hunt."""
    tools = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html'
        }
        response = requests.get(
            "https://www.producthunt.com/topics/artificial-intelligence",
            headers=headers,
            timeout=30
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract product information
        products = soup.find_all('div', {'data-test': 'product-item'})
        for product in products[:5]:
            try:
                name_elem = product.find('h3') or product.find('a', {'data-test': 'product-name'})
                desc_elem = product.find('p') or product.find('div', {'data-test': 'product-description'})
                
                if name_elem:
                    tools.append({
                        "name": name_elem.text.strip(),
                        "description": desc_elem.text.strip()[:200] if desc_elem else "AI product from Product Hunt",
                        "category": "Automation & Productivity",
                        "url": "https://www.producthunt.com",
                        "pricing": "Freemium"
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"Product Hunt scraping failed: {e}")
    
    return tools


def get_fallback_tools(count: int, existing_names: set) -> List[Dict]:
    """Get tools from fallback list, filtering out existing ones."""
    available = [
        tool for tool in FALLBACK_TOOLS
        if tool["name"].lower() not in existing_names
    ]
    return random.sample(available, min(count, len(available)))


def add_tools_to_database(data: Dict, new_tools: List[Dict]) -> int:
    """Add new tools to the database with proper IDs and metadata."""
    existing_names = get_existing_tool_names(data)
    added_count = 0
    today = datetime.now().strftime("%Y-%m-%d")
    
    for tool in new_tools:
        # Skip if already exists
        if tool["name"].lower() in existing_names:
            continue
        
        # Add metadata
        tool["id"] = generate_tool_id(data)
        tool["date_added"] = today
        tool["is_new"] = True
        tool["featured"] = False
        
        # Ensure description isn't too long
        if len(tool["description"]) > 200:
            tool["description"] = tool["description"][:197] + "..."
        
        data["tools"].append(tool)
        existing_names.add(tool["name"].lower())
        added_count += 1
    
    # Reset is_new flag on older tools (keep last 7 days as "new")
    for tool in data["tools"]:
        tool_date = datetime.strptime(tool["date_added"], "%Y-%m-%d")
        days_since = (datetime.now() - tool_date).days
        tool["is_new"] = days_since <= 7
    
    return added_count


def main():
    print("AI Tools Directory Auto-Updater")
    print("=" * 50)
    
    # Load existing database
    data = load_database()
    existing_count = len(data["tools"])
    print(f"Current tools in database: {existing_count}")
    
    # Try to scrape from various sources
    new_tools = []
    sources_attempted = []
    
    # Attempt 1: GitHub Trending
    print("\nScraping GitHub Trending...")
    github_tools = scrape_github_trending()
    if github_tools:
        new_tools.extend(github_tools)
        sources_attempted.append("GitHub")
        print(f"  Found {len(github_tools)} potential tools")
    
    # Attempt 2: Product Hunt
    print("Scraping Product Hunt...")
    ph_tools = scrape_product_hunt()
    if ph_tools:
        new_tools.extend(ph_tools)
        sources_attempted.append("ProductHunt")
        print(f"  Found {len(ph_tools)} potential tools")
    
    # If scraping didn't yield enough tools, use fallback
    existing_names = get_existing_tool_names(data)
    needed = TOOLS_TO_ADD_PER_RUN - len(new_tools)
    
    if needed > 0:
        print(f"\nUsing {needed} tools from fallback list...")
        fallback = get_fallback_tools(needed, existing_names)
        new_tools.extend(fallback)
        sources_attempted.append("FallbackDB")
    
    # Limit to desired count
    new_tools = new_tools[:TOOLS_TO_ADD_PER_RUN]
    
    # Add tools to database
    added = add_tools_to_database(data, new_tools)
    
    if added > 0:
        # Save updated database
        save_database(data)
        log_update(added, " + ".join(sources_attempted), f"Added tools: {[t['name'] for t in new_tools[:added]]}")
        print(f"\nSuccessfully added {added} new tools!")
        print(f"Total tools now: {len(data['tools'])}")
        print(f"Sources: {', '.join(sources_attempted)}")
        print(f"\nNew tools added:")
        for tool in new_tools[:added]:
            print(f"  • {tool['name']} ({tool['category']})")
    else:
        print("\nNo new tools added (all were duplicates or no tools found)")
        log_update(0, "None", "No new unique tools found")
    
    print(f"\nLast updated: {data['metadata']['last_updated']}")
    return 0 if added > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
