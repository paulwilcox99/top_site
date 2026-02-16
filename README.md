# Top-Level Site Aggregator

A unified dashboard portal that aggregates statistics and recent items from multiple static site collections (Books, Albums, and Broadway Shows). Provides a single entry point to browse all your collections with smart regeneration and flexible deployment options.

## Features

- **📊 Aggregate Statistics**: View total items, collection count, and overall average ratings across all collections
- **🎨 Collection Cards**: Individual cards for each collection showing detailed stats and recent additions
- **🔄 Smart Regeneration**: Only regenerates when databases change, using MD5 hash tracking
- **🌐 Flexible Deployment**: Works with both `file://` protocol and web servers (`http://`)
- **📱 Responsive Design**: Mobile-friendly layout that adapts to different screen sizes
- **🎯 Collection-Specific Styling**: Each collection has its own accent color and emoji
- **⚡ Fast & Lightweight**: Static HTML generation with embedded CSS

## Collections

This aggregator currently integrates three collections:

- **📚 Books**: Book collection with read/to-read status and ratings
- **🎵 Albums**: Music album collection with artists and genres
- **🎭 Broadway Shows**: Theater show collection with venues and dates

## Installation

### Prerequisites

- Python 3.x
- PyYAML library

```bash
pip install pyyaml
```

### Setup

1. Clone this repository:
```bash
git clone https://github.com/paulwilcox99/top_site.git
cd top_site
```

2. Ensure your collection databases are accessible at the paths specified in `config.yaml`

3. Make the generation script executable:
```bash
chmod +x generate_site.py
```

## Usage

### Basic Generation

```bash
# Smart regeneration (skips if databases unchanged)
python3 generate_site.py

# Force regeneration regardless of changes
python3 generate_site.py --force

# View help
python3 generate_site.py --help
```

### Viewing the Site

**File Protocol (default):**
```bash
# Open directly in browser
xdg-open site/index.html

# Or navigate to:
file:///path/to/top_site/site/index.html
```

**HTTP Protocol:**
1. Change `deployment_mode: 'http'` in `config.yaml`
2. Regenerate: `python3 generate_site.py --force`
3. Deploy to web server

## Configuration

Edit `config.yaml` to customize:

### Deployment Mode

```yaml
deployment_mode: 'file'  # or 'http'
```

- **file**: Uses relative paths (e.g., `../books/site/index.html`) for local browsing
- **http**: Uses absolute paths (e.g., `/books/index.html`) for web server deployment

### Adding New Collections

```yaml
collections:
  - name: "Collection Name"
    emoji: "🎬"
    db_path: "../path/to/database.db"
    site_path_file: "../path/to/site/index.html"
    site_path_http: "/path/index.html"
    accent_color: "#hexcolor"
    db_table: "table_name"
```

### Site Settings

```yaml
site:
  title: "My Collections"
  subtitle: "Books, Music & Theater"
  output_dir: "site"
  show_recent_items: true
  recent_items_count: 5
```

## How It Works

1. **Database Reading**: Connects to each collection's SQLite database and extracts statistics
2. **Aggregate Calculation**: Combines statistics across all collections (total items, average ratings)
3. **HTML Generation**: Creates a single static HTML page with embedded CSS
4. **Smart Regeneration**: Tracks database changes via MD5 hashing to skip unnecessary regeneration

### State Tracking

The `.site_state.json` file stores:
- Last generation timestamp
- Combined hash of all databases
- Individual hash for each database

Regeneration only occurs when database hashes change (unless `--force` is used).

## File Structure

```
top_site/
├── config.yaml           # Configuration file
├── generate_site.py      # Main generation script
├── site/                 # Generated output
│   └── index.html       # Portal dashboard
├── .site_state.json     # State tracking (auto-generated)
└── README.md            # This file
```

## Statistics Collected

### Books
- Total books
- Read count
- To-read count
- Average rating
- Recent additions (title, author)

### Albums
- Total albums
- Unique artists
- Average rating
- Recent additions (album, artist, rating)

### Broadway Shows
- Total shows
- Seen count
- Wishlist count
- Theater count
- Average rating
- Recent additions (show, theater, date, rating)

## Error Handling

The generator gracefully handles missing or inaccessible databases:
- Displays warning message
- Shows "Database not available" in collection card
- Continues processing other collections
- Adjusts aggregate statistics accordingly

## Design

The portal uses a clean, responsive design with:
- Georgia serif font for headings (classic, readable)
- System sans-serif for metadata and modern elements
- Collection-specific accent colors
- Gradient background for aggregate stats
- Card-based layout with hover effects
- Star ratings (★★★★★☆☆☆☆☆) for visual appeal

### Color Palette

- Primary: `#6366f1` (indigo)
- Books: `#8b2942` (burgundy)
- Albums: `#e91e63` (pink)
- Shows: `#c41e3a` (crimson)

## Development

The generation script follows patterns established in the individual collection generators:
- MD5-based change detection
- SQLite database access with error handling
- Static HTML generation with embedded CSS
- JSON state persistence
- Command-line interface with argparse

## Example Output

```
Generating top-level site...
  Reading Books database...
    ✓ Found 4 items
  Reading Albums database...
    ✓ Found 4 items
  Reading Broadway Shows database...
    ✓ Found 3 items
  Generating HTML...

✓ Site generated successfully!
  Output: /path/to/top_site/site/index.html
  Total items: 11
  Overall avg rating: 9.0/10
```

## Future Enhancements

Potential additions for extensibility:
- More collection types (Movies, Recipes, etc.)
- Search functionality across collections
- Filtering by rating, date, or category
- Timeline view of recent activity
- Export to different formats (JSON, CSV)

## License

This is a personal project for aggregating collection sites.

## Author

Created with assistance from Claude Sonnet 4.5
