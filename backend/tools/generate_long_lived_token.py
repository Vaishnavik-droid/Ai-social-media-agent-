"""
Facebook / Instagram Long-Lived Token Generator
================================================
Run this script once to exchange your short-lived token for:
  1. A Long-Lived User Token  (valid 60 days)
  2. A Page Access Token      (NEVER expires - use this in .env!)

Usage:
    cd backend
    ..\.venv\Scripts\python.exe tools/generate_long_lived_token.py
"""

import os
import sys
import re
import datetime
import httpx

APP_ID = "2231204290777395"
GRAPH_BASE = "https://graph.facebook.com/v19.0"
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


def print_banner():
    print()
    print("=" * 60)
    print("  Facebook / Instagram Long-Lived Token Generator")
    print("=" * 60)
    print()


def exchange_for_long_lived(app_id: str, app_secret: str, short_token: str) -> str:
    """Exchange short-lived token for a 60-day long-lived token."""
    print("[1/3] Exchanging short-lived token for long-lived token...")
    url = f"{GRAPH_BASE}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token,
    }
    resp = httpx.get(url, params=params, timeout=15.0)
    data = resp.json()

    if "error" in data:
        print(f"\n  ERROR: {data['error']['message']}")
        print("  -> Check your App Secret and short-lived token.")
        sys.exit(1)

    long_token = data.get("access_token")
    expires_in = data.get("expires_in", 0)
    days = int(expires_in) // 86400 if expires_in else 60
    print(f"  OK! Long-lived token obtained (expires in ~{days} days)")
    return long_token


def get_page_token(long_token: str, target_page_id: str) -> str:
    """Get never-expiring Page Access Token from the long-lived user token."""
    print("[2/3] Fetching Page Access Token (never expires)...")
    url = f"{GRAPH_BASE}/me/accounts"
    params = {"access_token": long_token}
    resp = httpx.get(url, params=params, timeout=15.0)
    data = resp.json()

    if "error" in data:
        print(f"\n  ERROR: {data['error']['message']}")
        print("  -> Returning long-lived user token as fallback.")
        return long_token

    pages = data.get("data", [])
    if not pages:
        print("  No pages found. Using long-lived token.")
        return long_token

    page_token = None
    for page in pages:
        print(f"  Found page: {page.get('name')} (ID: {page.get('id')})")
        if page.get("id") == target_page_id:
            page_token = page.get("access_token")
            print(f"  Matched target page!")
            break

    if not page_token:
        page_token = pages[0].get("access_token")
        print(f"  Using first page: {pages[0].get('name')}")

    return page_token


def verify_token(token: str) -> dict:
    """Verify token and return debug info."""
    print("[3/3] Verifying final token...")
    url = f"{GRAPH_BASE}/debug_token"
    params = {"input_token": token, "access_token": token}
    resp = httpx.get(url, params=params, timeout=15.0)
    return resp.json().get("data", {})


def update_env(final_token: str):
    """Auto-update backend/.env with new tokens."""
    with open(ENV_PATH, "r") as f:
        content = f.read()

    content = re.sub(r"FACEBOOK_PAGE_ACCESS_TOKEN=.*", f"FACEBOOK_PAGE_ACCESS_TOKEN={final_token}", content)
    content = re.sub(r"INSTAGRAM_ACCESS_TOKEN=.*", f"INSTAGRAM_ACCESS_TOKEN={final_token}", content)

    with open(ENV_PATH, "w") as f:
        f.write(content)

    print("  backend/.env updated! Restart the backend server.")


def main():
    print_banner()

    print("Step 1: Get these from https://developers.facebook.com/apps/2231204290777395/settings/basic/")
    print()
    app_secret = input("  Enter App Secret: ").strip()
    if not app_secret:
        print("App Secret cannot be empty!")
        sys.exit(1)

    print()
    print("Step 2: Get short-lived token from https://developers.facebook.com/tools/explorer/")
    print("  (Make sure these permissions are checked:")
    print("   pages_manage_posts, pages_read_engagement, pages_show_list,")
    print("   instagram_basic, instagram_content_publish)")
    print()
    short_token = input("  Paste your short-lived token: ").strip()
    if not short_token:
        print("Token cannot be empty!")
        sys.exit(1)

    print()

    # Read current page ID from .env
    with open(ENV_PATH, "r") as f:
        env_content = f.read()
    m = re.search(r'FACEBOOK_PAGE_ID="?([^"\n]+)"?', env_content)
    page_id = m.group(1).strip() if m else ""

    # Step 1: Long-lived token
    long_token = exchange_for_long_lived(APP_ID, app_secret, short_token)

    # Step 2: Page token (never expires)
    final_token = get_page_token(long_token, page_id)

    # Step 3: Verify
    info = verify_token(final_token)
    expires_at = info.get("expires_at", 0)

    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print()

    if expires_at == 0:
        print("  Token Expiry  : NEVER EXPIRES (permanent Page Token)")
    else:
        exp_dt = datetime.datetime.fromtimestamp(expires_at)
        days_left = (exp_dt - datetime.datetime.now()).days
        print(f"  Token Expiry  : {exp_dt.strftime('%d %B %Y')} ({days_left} days left)")

    print(f"  Token Valid   : {info.get('is_valid', False)}")
    print(f"  Scopes        : {', '.join(info.get('scopes', []))}")
    print()
    print("  Add these to backend/.env:")
    print()
    print(f"  FACEBOOK_PAGE_ACCESS_TOKEN={final_token}")
    print(f"  INSTAGRAM_ACCESS_TOKEN={final_token}")
    print()

    update = input("  Auto-update backend/.env now? (y/n): ").strip().lower()
    if update == "y":
        update_env(final_token)
    else:
        print("  Manually copy the tokens above into backend/.env")

    print()
    print("  Done! Both Facebook and Instagram will use this permanent token.")
    print()


if __name__ == "__main__":
    main()
