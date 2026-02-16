#!/usr/bin/env python3
"""
Top-Level Site Aggregator
Generates a unified dashboard and navigation hub for all collection sites.
Only regenerates if any database has changed since last run.
"""

import os
import sys
import json
import sqlite3
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from html import escape

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

# Configuration
CONFIG_FILE = "config.yaml"
STATE_FILE = ".site_state.json"


def load_config():
    """Load configuration from YAML file."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Configuration file '{CONFIG_FILE}' not found.")
        sys.exit(1)

    with open(CONFIG_FILE, 'r') as f:
        return yaml.safe_load(f)


def get_db_hash(db_path):
    """Get hash of database file to detect changes."""
    if not os.path.exists(db_path):
        return None
    with open(db_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def get_combined_hash(collections):
    """Get combined hash of all databases."""
    hashes = []
    for collection in collections:
        db_path = collection['db_path']
        db_hash = get_db_hash(db_path)
        hashes.append(db_hash or "missing")

    combined = "|".join(hashes)
    return hashlib.md5(combined.encode()).hexdigest()


def load_state():
    """Load previous generation state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state):
    """Save generation state."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def parse_json_field(value):
    """Parse a JSON field, returning empty list if invalid."""
    if not value:
        return []
    try:
        result = json.loads(value)
        if isinstance(result, list):
            return result
        return [result]
    except:
        return [value] if value else []


def get_books_stats(db_path):
    """Get statistics from books database."""
    stats = {
        'available': False,
        'total_count': 0,
        'read_count': 0,
        'to_read_count': 0,
        'avg_rating': None,
        'recent_items': []
    }

    if not os.path.exists(db_path):
        return stats

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Total count
        cursor.execute("SELECT COUNT(*) as count FROM books")
        stats['total_count'] = cursor.fetchone()['count']

        # Read count
        cursor.execute("SELECT COUNT(*) as count FROM books WHERE read_status = 'read'")
        stats['read_count'] = cursor.fetchone()['count']

        # To-read count
        cursor.execute("SELECT COUNT(*) as count FROM books WHERE read_status = 'to_read'")
        stats['to_read_count'] = cursor.fetchone()['count']

        # Average rating
        cursor.execute("SELECT AVG(rating) as avg FROM books WHERE rating IS NOT NULL")
        result = cursor.fetchone()
        if result['avg']:
            stats['avg_rating'] = round(result['avg'], 1)

        # Recent items
        cursor.execute("""
            SELECT title, authors, rating, date_added
            FROM books
            ORDER BY date_added DESC
            LIMIT 5
        """)
        stats['recent_items'] = [dict(row) for row in cursor.fetchall()]

        stats['available'] = True
        conn.close()
    except Exception as e:
        print(f"Warning: Could not read books database: {e}")

    return stats


def get_albums_stats(db_path):
    """Get statistics from albums database."""
    stats = {
        'available': False,
        'total_count': 0,
        'artist_count': 0,
        'avg_rating': None,
        'recent_items': []
    }

    if not os.path.exists(db_path):
        return stats

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Total count
        cursor.execute("SELECT COUNT(*) as count FROM albums")
        stats['total_count'] = cursor.fetchone()['count']

        # Artist count (unique)
        cursor.execute("SELECT DISTINCT artists FROM albums WHERE artists IS NOT NULL")
        artists_set = set()
        for row in cursor.fetchall():
            artists_list = parse_json_field(row['artists'])
            for artist in artists_list:
                if artist and artist.strip():
                    artists_set.add(artist.strip())
        stats['artist_count'] = len(artists_set)

        # Average rating
        cursor.execute("SELECT AVG(rating) as avg FROM albums WHERE rating IS NOT NULL")
        result = cursor.fetchone()
        if result['avg']:
            stats['avg_rating'] = round(result['avg'], 1)

        # Recent items
        cursor.execute("""
            SELECT album_name, artists, genre, rating, date_added
            FROM albums
            ORDER BY date_added DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        for row in rows:
            item = dict(row)
            item['artists_list'] = parse_json_field(row['artists'])
            stats['recent_items'].append(item)

        stats['available'] = True
        conn.close()
    except Exception as e:
        print(f"Warning: Could not read albums database: {e}")

    return stats


def get_shows_stats(db_path):
    """Get statistics from shows database."""
    stats = {
        'available': False,
        'total_count': 0,
        'seen_count': 0,
        'wishlist_count': 0,
        'theater_count': 0,
        'avg_rating': None,
        'recent_items': []
    }

    if not os.path.exists(db_path):
        return stats

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Total count
        cursor.execute("SELECT COUNT(*) as count FROM shows")
        stats['total_count'] = cursor.fetchone()['count']

        # Seen count
        cursor.execute("SELECT COUNT(*) as count FROM shows WHERE seen_status = 'seen'")
        stats['seen_count'] = cursor.fetchone()['count']

        # Wishlist count
        cursor.execute("SELECT COUNT(*) as count FROM shows WHERE seen_status = 'wishlist'")
        stats['wishlist_count'] = cursor.fetchone()['count']

        # Theater count
        cursor.execute("SELECT COUNT(DISTINCT theater_name) as count FROM shows WHERE theater_name IS NOT NULL")
        stats['theater_count'] = cursor.fetchone()['count']

        # Average rating
        cursor.execute("SELECT AVG(rating) as avg FROM shows WHERE rating IS NOT NULL AND seen_status = 'seen'")
        result = cursor.fetchone()
        if result['avg']:
            stats['avg_rating'] = round(result['avg'], 1)

        # Recent items
        cursor.execute("""
            SELECT show_name, theater_name, date_attended, rating
            FROM shows
            WHERE seen_status = 'seen'
            ORDER BY date_attended DESC
            LIMIT 5
        """)
        stats['recent_items'] = [dict(row) for row in cursor.fetchall()]

        stats['available'] = True
        conn.close()
    except Exception as e:
        print(f"Warning: Could not read shows database: {e}")

    return stats


def get_restaurants_stats(db_path):
    """Get statistics from restaurants database."""
    stats = {
        'available': False,
        'total_count': 0,
        'visited_count': 0,
        'wishlist_count': 0,
        'location_count': 0,
        'avg_rating': None,
        'recent_items': []
    }

    if not os.path.exists(db_path):
        return stats

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Total count
        cursor.execute("SELECT COUNT(*) as count FROM restaurants")
        stats['total_count'] = cursor.fetchone()['count']

        # Visited count
        cursor.execute("SELECT COUNT(*) as count FROM restaurants WHERE visit_status = 'visited'")
        stats['visited_count'] = cursor.fetchone()['count']

        # Wishlist count
        cursor.execute("SELECT COUNT(*) as count FROM restaurants WHERE visit_status = 'want_to_visit'")
        stats['wishlist_count'] = cursor.fetchone()['count']

        # Location count
        cursor.execute("SELECT COUNT(DISTINCT location) as count FROM restaurants WHERE location IS NOT NULL")
        stats['location_count'] = cursor.fetchone()['count']

        # Average rating
        cursor.execute("SELECT AVG(rating) as avg FROM restaurants WHERE rating IS NOT NULL AND visit_status = 'visited'")
        result = cursor.fetchone()
        if result['avg']:
            stats['avg_rating'] = round(result['avg'], 1)

        # Recent items
        cursor.execute("""
            SELECT restaurant_name, location, cuisine, rating, date_added
            FROM restaurants
            ORDER BY date_added DESC
            LIMIT 5
        """)
        stats['recent_items'] = [dict(row) for row in cursor.fetchall()]

        stats['available'] = True
        conn.close()
    except Exception as e:
        print(f"Warning: Could not read restaurants database: {e}")

    return stats


def calculate_aggregate_stats(collections_stats):
    """Calculate aggregate statistics across all collections."""
    total_items = sum(stats.get('total_count', 0) for stats in collections_stats.values())

    # Calculate overall average rating
    ratings = []
    for stats in collections_stats.values():
        if stats.get('avg_rating'):
            ratings.append(stats['avg_rating'])

    overall_avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

    return {
        'total_items': total_items,
        'overall_avg_rating': overall_avg_rating,
        'collection_count': len([s for s in collections_stats.values() if s.get('available')])
    }


def generate_star_rating(rating, max_rating=10):
    """Generate star rating HTML."""
    if not rating:
        return '<span style="color: #999;">No rating</span>'

    filled = int(rating)
    empty = max_rating - filled
    stars = "★" * filled + "☆" * empty
    return f'<span class="rating">{stars}</span> <span style="font-size: 0.9rem;">{rating}/{max_rating}</span>'


def generate_recent_item_card(item, collection_name):
    """Generate HTML for a recent item mini card."""
    html = '<div class="recent-item">'

    if collection_name == "Books":
        title = escape(item.get('title', 'Unknown'))
        authors = escape(item.get('authors', 'Unknown'))
        rating = item.get('rating')
        html += f'<div class="recent-item-title">{title}</div>'
        html += f'<div class="recent-item-meta">{authors}</div>'
        if rating:
            html += f'<div class="recent-item-rating">{generate_star_rating(rating)}</div>'

    elif collection_name == "Albums":
        album = escape(item.get('album_name', 'Unknown'))
        artists = item.get('artists_list', [])
        artist_str = ", ".join(artists) if artists else item.get('artists', 'Unknown')
        rating = item.get('rating')
        html += f'<div class="recent-item-title">{album}</div>'
        html += f'<div class="recent-item-meta">{escape(artist_str)}</div>'
        if rating:
            html += f'<div class="recent-item-rating">{generate_star_rating(rating)}</div>'

    elif collection_name == "Broadway Shows":
        show = escape(item.get('show_name', 'Unknown'))
        theater = escape(item.get('theater_name', 'Unknown'))
        date = item.get('date_attended', '')
        rating = item.get('rating')
        html += f'<div class="recent-item-title">{show}</div>'
        html += f'<div class="recent-item-meta">{theater}'
        if date:
            html += f' • {date}'
        html += '</div>'
        if rating:
            html += f'<div class="recent-item-rating">{generate_star_rating(rating)}</div>'

    elif collection_name == "Restaurants":
        restaurant = escape(item.get('restaurant_name', 'Unknown'))
        location = escape(item.get('location', 'Unknown'))
        cuisine = escape(item.get('cuisine', ''))
        rating = item.get('rating')
        html += f'<div class="recent-item-title">{restaurant}</div>'
        html += f'<div class="recent-item-meta">{location}'
        if cuisine:
            html += f' • {cuisine}'
        html += '</div>'
        if rating:
            html += f'<div class="recent-item-rating">{generate_star_rating(rating)}</div>'

    html += '</div>'
    return html


def generate_collection_card(collection, stats, config):
    """Generate HTML for a collection card."""
    name = collection['name']
    emoji = collection['emoji']
    accent_color = collection['accent_color']

    # Determine link path based on deployment mode
    deployment_mode = config.get('deployment_mode', 'file')
    if deployment_mode == 'http':
        link_path = collection['site_path_http']
    else:
        link_path = collection['site_path_file']

    html = f'<div class="collection-card" style="--collection-accent: {accent_color};">'
    html += f'<div class="collection-header">'
    html += f'<span class="collection-emoji">{emoji}</span>'
    html += f'<h2 class="collection-name">{escape(name)}</h2>'
    html += '</div>'

    if not stats['available']:
        html += '<div class="collection-unavailable">Database not available</div>'
    else:
        # Statistics section
        html += '<div class="collection-stats">'

        if name == "Books":
            html += f'<div class="stat-item"><span class="stat-value">{stats["total_count"]}</span><span class="stat-label">Total Books</span></div>'
            html += f'<div class="stat-item"><span class="stat-value">{stats["read_count"]}</span><span class="stat-label">Read</span></div>'
            html += f'<div class="stat-item"><span class="stat-value">{stats["to_read_count"]}</span><span class="stat-label">To Read</span></div>'
            if stats['avg_rating']:
                html += f'<div class="stat-item"><span class="stat-value">{stats["avg_rating"]}</span><span class="stat-label">Avg Rating</span></div>'

        elif name == "Albums":
            html += f'<div class="stat-item"><span class="stat-value">{stats["total_count"]}</span><span class="stat-label">Albums</span></div>'
            html += f'<div class="stat-item"><span class="stat-value">{stats["artist_count"]}</span><span class="stat-label">Artists</span></div>'
            if stats['avg_rating']:
                html += f'<div class="stat-item"><span class="stat-value">{stats["avg_rating"]}</span><span class="stat-label">Avg Rating</span></div>'

        elif name == "Broadway Shows":
            html += f'<div class="stat-item"><span class="stat-value">{stats["total_count"]}</span><span class="stat-label">Total Shows</span></div>'
            html += f'<div class="stat-item"><span class="stat-value">{stats["seen_count"]}</span><span class="stat-label">Seen</span></div>'
            html += f'<div class="stat-item"><span class="stat-value">{stats["wishlist_count"]}</span><span class="stat-label">Wishlist</span></div>'
            if stats['avg_rating']:
                html += f'<div class="stat-item"><span class="stat-value">{stats["avg_rating"]}</span><span class="stat-label">Avg Rating</span></div>'

        elif name == "Restaurants":
            html += f'<div class="stat-item"><span class="stat-value">{stats["total_count"]}</span><span class="stat-label">Restaurants</span></div>'
            html += f'<div class="stat-item"><span class="stat-value">{stats["visited_count"]}</span><span class="stat-label">Visited</span></div>'
            html += f'<div class="stat-item"><span class="stat-value">{stats["wishlist_count"]}</span><span class="stat-label">Wishlist</span></div>'
            if stats['avg_rating']:
                html += f'<div class="stat-item"><span class="stat-value">{stats["avg_rating"]}</span><span class="stat-label">Avg Rating</span></div>'

        html += '</div>'

        # Recent items section
        if stats['recent_items'] and config['site'].get('show_recent_items', True):
            html += '<div class="recent-section">'
            html += '<h3 class="recent-title">Recently Added</h3>'
            html += '<div class="recent-items">'
            for item in stats['recent_items'][:config['site'].get('recent_items_count', 5)]:
                html += generate_recent_item_card(item, name)
            html += '</div>'
            html += '</div>'

    # Browse button
    html += f'<a href="{link_path}" class="browse-button">Browse {escape(name)} →</a>'
    html += '</div>'

    return html


def generate_html(config, collections_stats, aggregate_stats):
    """Generate complete HTML page."""
    site_config = config['site']
    title = site_config['title']
    subtitle = site_config.get('subtitle', '')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <style>
        :root {{
            --primary: #6366f1;
            --text: #2c3e50;
            --text-muted: #7f8c8d;
            --bg: #ffffff;
            --bg-card: #f8f9fa;
            --border: #e0e0e0;
            --border-light: #f0f0f0;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: Georgia, serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 2px solid var(--border);
        }}

        h1 {{
            font-size: 2.5rem;
            color: var(--primary);
            font-weight: normal;
            margin-bottom: 0.5rem;
        }}

        .subtitle {{
            font-size: 1.1rem;
            color: var(--text-muted);
            font-style: italic;
        }}

        .aggregate-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            border-radius: 8px;
            border: 1px solid var(--border-light);
        }}

        .aggregate-stat {{
            text-align: center;
        }}

        .aggregate-stat-value {{
            font-size: 3rem;
            color: var(--primary);
            font-weight: normal;
            font-family: Georgia, serif;
        }}

        .aggregate-stat-label {{
            font-size: 0.9rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin-top: 0.5rem;
        }}

        .collections {{
            display: grid;
            gap: 2rem;
        }}

        .collection-card {{
            background: var(--bg-card);
            border: 2px solid var(--border);
            border-radius: 8px;
            padding: 2rem;
            transition: all 0.2s ease;
        }}

        .collection-card:hover {{
            border-color: var(--collection-accent);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}

        .collection-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--collection-accent);
        }}

        .collection-emoji {{
            font-size: 2.5rem;
        }}

        .collection-name {{
            font-size: 1.8rem;
            font-weight: normal;
            color: var(--collection-accent);
        }}

        .collection-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .stat-item {{
            text-align: center;
            padding: 1rem;
            background: var(--bg);
            border-radius: 6px;
        }}

        .stat-value {{
            display: block;
            font-size: 2rem;
            color: var(--collection-accent);
            font-weight: normal;
            font-family: Georgia, serif;
        }}

        .stat-label {{
            display: block;
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin-top: 0.5rem;
        }}

        .recent-section {{
            margin-bottom: 2rem;
        }}

        .recent-title {{
            font-size: 1.2rem;
            color: var(--text);
            margin-bottom: 1rem;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}

        .recent-items {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }}

        .recent-item {{
            background: var(--bg);
            padding: 1rem;
            border: 1px solid var(--border);
            border-radius: 6px;
            transition: all 0.2s ease;
        }}

        .recent-item:hover {{
            border-color: var(--collection-accent);
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        }}

        .recent-item-title {{
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}

        .recent-item-meta {{
            font-size: 0.9rem;
            color: var(--text-muted);
            font-style: italic;
            margin-bottom: 0.5rem;
        }}

        .recent-item-rating {{
            font-size: 0.85rem;
            color: var(--collection-accent);
        }}

        .rating {{
            color: var(--collection-accent);
        }}

        .browse-button {{
            display: inline-block;
            background: var(--collection-accent);
            color: white;
            padding: 0.75rem 2rem;
            text-decoration: none;
            border-radius: 6px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.2s ease;
        }}

        .browse-button:hover {{
            opacity: 0.9;
            transform: translateX(4px);
        }}

        .collection-unavailable {{
            padding: 2rem;
            text-align: center;
            color: var(--text-muted);
            font-style: italic;
            background: var(--bg);
            border-radius: 6px;
            margin-bottom: 1rem;
        }}

        footer {{
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 0.85rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            text-align: center;
        }}

        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            h1 {{ font-size: 2rem; }}
            .collection-stats {{ grid-template-columns: repeat(2, 1fr); }}
            .recent-items {{ grid-template-columns: 1fr; }}
            .aggregate-stats {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{escape(title)}</h1>'''

    if subtitle:
        html += f'\n        <div class="subtitle">{escape(subtitle)}</div>'

    html += '''
    </div>

    <div class="aggregate-stats">'''

    # Aggregate statistics
    html += f'''
        <div class="aggregate-stat">
            <div class="aggregate-stat-value">{aggregate_stats["total_items"]}</div>
            <div class="aggregate-stat-label">Total Items</div>
        </div>
        <div class="aggregate-stat">
            <div class="aggregate-stat-value">{aggregate_stats["collection_count"]}</div>
            <div class="aggregate-stat-label">Collections</div>
        </div>'''

    if aggregate_stats['overall_avg_rating']:
        html += f'''
        <div class="aggregate-stat">
            <div class="aggregate-stat-value">{aggregate_stats["overall_avg_rating"]}</div>
            <div class="aggregate-stat-label">Overall Avg Rating</div>
        </div>'''

    html += '''
    </div>

    <div class="collections">'''

    # Collection cards
    for collection in config['collections']:
        collection_name = collection['name']
        stats = collections_stats.get(collection_name, {})
        html += generate_collection_card(collection, stats, config)

    html += f'''
    </div>

    <footer>
        Generated on {timestamp}
    </footer>
</body>
</html>'''

    return html


def generate_site(config, force=False):
    """Main site generation function."""
    collections = config['collections']

    # Check if regeneration is needed
    current_hash = get_combined_hash(collections)
    state = load_state()

    if not force and state.get('databases_hash') == current_hash:
        print("✓ No database changes detected. Site is up to date.")
        print(f"  Use --force to regenerate anyway.")
        return False

    print("Generating top-level site...")

    # Gather statistics from all collections
    collections_stats = {}
    for collection in collections:
        name = collection['name']
        db_path = collection['db_path']
        db_table = collection['db_table']

        print(f"  Reading {name} database...")

        if db_table == 'books':
            stats = get_books_stats(db_path)
        elif db_table == 'albums':
            stats = get_albums_stats(db_path)
        elif db_table == 'shows':
            stats = get_shows_stats(db_path)
        elif db_table == 'restaurants':
            stats = get_restaurants_stats(db_path)
        else:
            print(f"    Warning: Unknown collection type '{db_table}'")
            stats = {'available': False}

        collections_stats[name] = stats

        if stats['available']:
            print(f"    ✓ Found {stats.get('total_count', 0)} items")
        else:
            print(f"    ⚠ Database not available")

    # Calculate aggregate statistics
    aggregate_stats = calculate_aggregate_stats(collections_stats)

    # Generate HTML
    print("  Generating HTML...")
    html = generate_html(config, collections_stats, aggregate_stats)

    # Write output
    output_dir = config['site']['output_dir']
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, 'index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # Save state
    individual_hashes = {}
    for collection in collections:
        name = collection['name']
        db_path = collection['db_path']
        individual_hashes[name] = get_db_hash(db_path)

    new_state = {
        'last_generated': datetime.now().isoformat(),
        'databases_hash': current_hash,
        'individual_hashes': individual_hashes
    }
    save_state(new_state)

    print(f"\n✓ Site generated successfully!")
    print(f"  Output: {os.path.abspath(output_path)}")
    print(f"  Total items: {aggregate_stats['total_items']}")
    if aggregate_stats['overall_avg_rating']:
        print(f"  Overall avg rating: {aggregate_stats['overall_avg_rating']}/10")

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate top-level collection site aggregator',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force regeneration even if databases unchanged')

    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Generate site
    generate_site(config, force=args.force)


if __name__ == '__main__':
    main()
