#!/usr/bin/env python3
"""Query Polymarket prediction markets via the Gamma API."""

import json
import sys
import urllib.request
import urllib.parse

BASE_URL = "https://gamma-api.polymarket.com"

def fetch(endpoint: str, params: dict = None) -> dict | list:
    url = f"{BASE_URL}{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Clawdbot-Polymarket/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

def trending():
    """Get trending/active markets."""
    markets = fetch("/markets", {"limit": "15", "active": "true", "order": "volume24hr", "ascending": "false"})
    print("📊 Trending Polymarket Markets\n")
    for m in markets:
        question = m.get("question", "Unknown")
        volume = float(m.get("volume", 0) or 0)
        volume_24h = float(m.get("volume24hr", 0) or 0)
        end_date = m.get("endDate", "")[:10]
        
        # Get outcome prices
        outcomes = m.get("outcomePrices", "[]")
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except:
                outcomes = []
        
        yes_price = float(outcomes[0]) * 100 if len(outcomes) > 0 else 0
        no_price = float(outcomes[1]) * 100 if len(outcomes) > 1 else 0
        
        print(f"  {question}")
        print(f"    YES: {yes_price:.0f}% | NO: {no_price:.0f}% | Vol: ${volume:,.0f} | 24h: ${volume_24h:,.0f} | Ends: {end_date}")
        print()

def search(query: str):
    """Search markets by query."""
    markets = fetch("/markets", {"limit": "10", "active": "true", "closed": "false", "query": query})
    print(f"🔍 Search results for '{query}'\n")
    if not markets:
        print("  No markets found.")
        return
    for m in markets:
        question = m.get("question", "Unknown")
        volume = float(m.get("volume", 0) or 0)
        outcomes = m.get("outcomePrices", "[]")
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except:
                outcomes = []
        yes_price = float(outcomes[0]) * 100 if len(outcomes) > 0 else 0
        slug = m.get("slug", "")
        print(f"  {question}")
        print(f"    YES: {yes_price:.0f}% | Vol: ${volume:,.0f} | Slug: {slug}")
        print()

def event(slug: str):
    """Get a specific event/market by slug."""
    events = fetch("/events", {"slug": slug})
    if not events:
        print(f"  Event '{slug}' not found.")
        return
    e = events[0] if isinstance(events, list) else events
    print(f"📊 {e.get('title', slug)}\n")
    print(f"  Description: {e.get('description', 'N/A')[:300]}")
    print(f"  End: {e.get('endDate', 'N/A')[:10]}")
    print(f"  Volume: ${e.get('volume', 0):,.0f}")
    print()
    markets = e.get("markets", [])
    for m in markets:
        question = m.get("question", "?")
        outcomes = m.get("outcomePrices", "[]")
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except:
                outcomes = []
        yes = float(outcomes[0]) * 100 if len(outcomes) > 0 else 0
        print(f"  → {question}: YES {yes:.0f}%")

def category(cat: str):
    """Get markets by category tag."""
    markets = fetch("/markets", {"limit": "10", "active": "true", "tag": cat, "order": "volume24hr", "ascending": "false"})
    print(f"📂 Category: {cat}\n")
    if not markets:
        print("  No markets found.")
        return
    for m in markets:
        question = m.get("question", "Unknown")
        volume = float(m.get("volume", 0) or 0)
        outcomes = m.get("outcomePrices", "[]")
        if isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except:
                outcomes = []
        yes_price = float(outcomes[0]) * 100 if len(outcomes) > 0 else 0
        print(f"  {question}")
        print(f"    YES: {yes_price:.0f}% | Vol: ${volume:,.0f}")
        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: polymarket.py <trending|search|event|category> [query]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    arg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    
    try:
        if cmd == "trending":
            trending()
        elif cmd == "search":
            search(arg)
        elif cmd == "event":
            event(arg)
        elif cmd == "category":
            category(arg)
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
