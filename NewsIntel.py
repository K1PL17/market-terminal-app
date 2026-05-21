# -*- coding: utf-8 -*-
import feedparser
from datetime import datetime, timedelta
import time
import os
import html
from flask import Flask

# Inisialisasi Aplikasi Flask
app = Flask(__name__)

# 1. Konfigurasi RSS Feeds
FEEDS = {
    'Indonesia': {
        'CNBC Indonesia': 'https://www.cnbcindonesia.com/news/rss',
        'Detikcom': 'https://rss.detik.com/index.php/detikcom',
        'Antara News': 'https://www.antaranews.com/rss/top-news.xml'
    },
    'Mancanegara': {
        'Yahoo Finance': 'https://finance.yahoo.com/news/rssindex',
        'BBC World': 'http://feeds.bbci.co.uk/news/world/rss.xml',
        'Business Insider': 'https://www.businessinsider.com/sai/rss'
    }
}

# 2. Kata Kunci untuk Kategorisasi
KEYWORDS = {
    'Politik': ['politik', 'pemilu', ' DPR ', 'presiden', 'menteri', 'governance', 'election', 'minister', 'government', 'bupati', 'gubernur'],
    'Ekonomi': ['ekonomi', 'inflasi', 'PDB', 'pertumbuhan', 'economy', 'gdp', 'inflation', 'recession', 'resesi', 'stimulus'],
    'Keuangan': ['keuangan', 'saham', 'investasi', 'pasar modal', 'finance', 'stocks', 'investment', 'market', 'obligasi', 'bursa'],
    'Perbankan': ['bank', 'suku bunga', 'bi rate', 'fed rate', 'banking', 'interest rate', 'kredit', 'nasabah', 'ojk'],
    'Komoditas': ['komoditas', 'cpo', 'kelapa sawit', 'minyak goreng', 'gandum', 'commodity', 'agriculture', 'pangan', 'beras'],
    'Hasil Tambang': ['tambang', 'batu bara', 'nikel', 'emas', 'tembaga', 'mining', 'coal', 'nickel', 'gold', 'bauxite', 'timah']
}

def parse_date(entry):
    for date_key in ['published_parsed', 'updated_parsed', 'created_parsed']:
        if date_key in entry and entry[date_key] is not None:
            return datetime.fromtimestamp(time.mktime(entry[date_key]))
    return datetime.now()

def categorize_article(title, summary):
    text = f"{title} {summary}".lower()
    matched_categories = []
    for category, keywords in KEYWORDS.items():
        if any(kw.lower() in text for kw in keywords):
            matched_categories.append(category)
    return matched_categories if matched_categories else ['Lainnya']

def fetch_news():
    now = datetime.now()
    one_day_ago = now - timedelta(hours=24)
    all_news = []
    stats = {cat: 0 for cat in KEYWORDS.keys()}
    stats['Lainnya'] = 0
    geo_stats = {'Indonesia': 0, 'Mancanegara': 0}

    for region, sources in FEEDS.items():
        for source_name, url in sources.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    pub_date = parse_date(entry)
                    if pub_date >= one_day_ago:
                        title = entry.get('title', 'No Title')
                        summary = entry.get('summary', entry.get('description', ''))
                        link = entry.get('link', '#')
                        categories = categorize_article(title, summary)

                        if any(cat in KEYWORDS.keys() for cat in categories):
                            for cat in categories:
                                stats[cat] += 1
                            geo_stats[region] += 1

                            all_news.append({
                                'title': title,
                                'summary': summary,
                                'link': link,
                                'source': source_name,
                                'region': region,
                                'time': pub_date.strftime('%H:%M'),
                                'categories': categories
                            })
            except Exception as e:
                print(f"Gagal mengambil data dari {source_name}: {e}")

    all_news.sort(key=lambda x: x['time'], reverse=True)
    return all_news, stats, geo_stats

def generate_html_string(news_data, stats, geo_stats):
    total_news = len(news_data)
    cards_html = ""
    
    if not news_data:
        cards_html = "<div class='no-news'>Tidak ada berita yang ditemukan dalam 24 jam terakhir untuk kategori ini.</div>"
    else:
        for item in news_data:
            cat_badges = "".join([f"<span class='badge'>{c}</span>" for c in item['categories'] if c != 'Lainnya'])
            region_class = 'badge-id' if item['region'] == 'Indonesia' else 'badge-global'

            cards_html += f"""
            <div class="news-card" data-categories='{html.escape(str(item['categories']))}'>
                <div class="card-meta">
                    <span class="badge-geo {region_class}">{item['region']}</span>
                    <span class="source">{item['source']}</span>
                    <span class="time">🕒 {item['time']}</span>
                </div>
                <a href="{item['link']}" target="_blank" class="card-title">{html.escape(item['title'])}</a>
                <p class="card-summary">{html.escape(item['summary'][:200])}...</p>
                <div class="card-tags">
                    {cat_badges}
                </div>
            </div>
            """

    stats_html = ""
    for cat, count in stats.items():
        if cat != 'Lainnya':
            stats_html += f"""
            <div class="stat-box">
                <span class="stat-label">{cat}</span>
                <span class="stat-value">{count}</span>
            </div>
            """

    # Mengembalikan string HTML langsung, bukan menulis ke file
    return f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MARKET INSIGHTS TERMINAL</title>
        <style>
            :root {{ --bg-dark: #0B0E14; --panel-bg: #151A22; --border-color: #262F3D; --text-main: #E2E8F0; --text-muted: #8A99AD; --accent-green: #00E676; --accent-blue: #00B0FF; --accent-orange: #FF9100; }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Courier, monospace; }}
            body {{ background-color: var(--bg-dark); color: var(--text-main); padding: 20px; }}
            header {{ display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 2px solid var(--border-color); margin-bottom: 25px; }}
            .logo {{ font-size: 24px; font-weight: bold; color: var(--accent-green); letter-spacing: 1px; }}
            .logo span {{ color: var(--text-main); }}
            .timestamp {{ color: var(--text-muted); font-size: 14px; }}
            .dashboard-grid {{ display: grid; grid-template-columns: 1fr 3fr; gap: 20px; }}
            .sidebar {{ display: flex; flex-direction: column; gap: 20px; }}
            .panel {{ background-color: var(--panel-bg); border: 1px solid var(--border-color); padding: 20px; border-radius: 4px; }}
            .panel-title {{ font-size: 14px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 15px; letter-spacing: 0.5px; border-left: 3px solid var(--accent-green); padding-left: 8px; }}
            .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
            .stat-box {{ background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); padding: 12px; border-radius: 4px; text-align: center; }}
            .stat-label {{ display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 5px; }}
            .stat-value {{ font-size: 20px; font-weight: bold; color: var(--accent-blue); }}
            .geo-box {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; padding: 5px 0; border-bottom: 1px dashed var(--border-color); }}
            .feed-container {{ display: flex; flex-direction: column; gap: 15px; }}
            .filter-bar {{ display: flex; gap: 10px; overflow-x: auto; padding-bottom: 10px; }}
            .filter-btn {{ background: transparent; border: 1px solid var(--border-color); color: var(--text-muted); padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 13px; transition: 0.2s; }}
            .filter-btn.active, .filter-btn:hover {{ background: var(--accent-green); color: var(--bg-dark); font-weight: bold; border-color: var(--accent-green); }}
            .news-card {{ background-color: var(--panel-bg); border: 1px solid var(--border-color); padding: 20px; border-radius: 4px; transition: transform 0.2s, border-color 0.2s; }}
            .news-card:hover {{ border-color: var(--text-muted); transform: translateY(-2px); }}
            .card-meta {{ display: flex; align-items: center; gap: 10px; font-size: 12px; margin-bottom: 10px; color: var(--text-muted); }}
            .badge-geo {{ padding: 2px 6px; border-radius: 2px; font-weight: bold; color: #fff; }}
            .badge-id {{ background-color: #D32F2F; }}
            .badge-global {{ background-color: #1976D2; }}
            .source {{ font-weight: bold; color: var(--text-main); }}
            .card-title {{ font-size: 18px; font-weight: 600; color: var(--text-main); text-decoration: none; display: block; margin-bottom: 10px; line-height: 1.4; }}
            .card-title:hover {{ color: var(--accent-green); }}
            .card-summary {{ font-size: 14px; color: var(--text-muted); line-height: 1.6; margin-bottom: 15px; }}
            .card-tags .badge {{ background: rgba(0, 176, 255, 0.1); color: var(--accent-blue); border: 1px solid rgba(0, 176, 255, 0.3); font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-right: 5px; }}
            .no-news {{ text-align: center; padding: 40px; color: var(--text-muted); border: 1px dashed var(--border-color); }}
            @media (max-width: 768px) {{ .dashboard-grid {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <header>
            <div class="logo">MARKET_<span>TERMINAL.IDX</span></div>
            <div class="timestamp">Terakhir Diperbarui: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (24H Window)</div>
        </header>
        <div class="dashboard-grid">
            <div class="sidebar">
                <div class="panel">
                    <div class="panel-title">Volume Kategori (24 Jam)</div>
                    <div class="stat-grid">{stats_html}</div>
                </div>
                <div class="panel">
                    <div class="panel-title">Distribusi Wilayah</div>
                    <div class="geo-box"><span>Indonesia</span><span style="font-weight:bold; color: var(--accent-orange);">{geo_stats['Indonesia']} Berita</span></div>
                    <div class="geo-box"><span>Mancanegara</span><span style="font-weight:bold; color: var(--accent-blue);">{geo_stats['Mancanegara']} Berita</span></div>
                </div>
                <div class="panel">
                    <div class="panel-title">Ringkasan Eksekutif</div>
                    <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5;">Terminal mendeteksi total <b>{total_news}</b> sentimen berita krusial dalam 24 jam terakhir.</p>
                </div>
            </div>
            <div class="feed-container">
                <div class="filter-bar">
                    <button class="filter-btn active" onclick="filterCategory('Semua')">Semua Sektor</button>
                    <button class="filter-btn" onclick="filterCategory('Politik')">Politik</button>
                    <button class="filter-btn" onclick="filterCategory('Ekonomi')">Ekonomi</button>
                    <button class="filter-btn" onclick="filterCategory('Keuangan')">Keuangan</button>
                    <button class="filter-btn" onclick="filterCategory('Perbankan')">Perbankan</button>
                    <button class="filter-btn" onclick="filterCategory('Komoditas')">Komoditas</button>
                    <button class="filter-btn" onclick="filterCategory('Hasil Tambang')">Hasil Tambang</button>
                </div>
                <div id="news-feed">{cards_html}</div>
            </div>
        </div>
        <script>
            function filterCategory(category) {{
                const buttons = document.querySelectorAll('.filter-btn');
                buttons.forEach(btn => btn.classList.remove('active'));
                event.target.classList.add('active');
                const cards = document.querySelectorAll('.news-card');
                cards.forEach(card => {{
                    if (category === 'Semua') {{
                        card.style.display = 'block';
                    }} else {{
                        const itemCategories = JSON.parse(card.getAttribute('data-categories').replace(/'/g, '"'));
                        if (itemCategories.includes(category)) {{
                            card.style.display = 'block';
                        }} else {{
                            card.style.display = 'none';
                        }}
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    """

# 3. Route Utama Web
@app.route("/")
def index():
    print("Menerima request, mengambil berita terbaru...")
    news, stats, geo_stats = fetch_news()
    html_content = generate_html_string(news, stats, geo_stats)
    return html_content

if __name__ == "__main__":
    # Konfigurasi Port Dinamis (Penting untuk Production/Deployment)
    port = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' membuat server dapat diakses dari luar localhost
    app.run(host='0.0.0.0', port=port, debug=True)