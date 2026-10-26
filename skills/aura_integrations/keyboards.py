"""
Aura Telegram Inline Keyboard Button Helpers for Hermes Agent.
Provides interactive buttons for news categories, scraping options, platform drafting, and stock analyses.
"""

def get_url_suggest_buttons(url: str) -> list:
    """Return inline keyboard row for scraped URL choices."""
    return [
        [
            {"text": "📰 Scrape Jadi Content", "callback_data": f"do_scrape:{url}"},
            {"text": "🔍 Info Pantas", "callback_data": f"do_summarize:{url}"}
        ]
    ]


def get_news_category_buttons() -> list:
    """Return inline keyboard matrix for news categories."""
    return [
        [
            {"text": "💻 Gajet & Tech", "callback_data": "gnews_cat:gajet"},
            {"text": "💼 Korporat", "callback_data": "gnews_cat:korporat"}
        ],
        [
            {"text": "🎭 Artis & Hiburan", "callback_data": "gnews_cat:artis"},
            {"text": "⚽ Sukan", "callback_data": "gnews_cat:sukan"}
        ],
        [
            {"text": "🔥 Viral & Confession", "callback_data": "viral_menu:0"},
            {"text": "⚡ Isu Semasa", "callback_data": "gnews_cat:nasional"}
        ]
    ]


def get_platform_selection_buttons(selected_platforms: list = None) -> list:
    """Return inline keyboard matrix for platform draft selection."""
    if selected_platforms is None:
        selected_platforms = []

    platforms = [
        ("Facebook", "facebook"),
        ("X (Twitter)", "x"),
        ("Threads", "threads"),
        ("Lemon8", "lemon8"),
        ("Instagram", "instagram")
    ]

    keyboard = []
    row = []
    for label, val in platforms:
        status = "✅ " if val in selected_platforms else "⬜ "
        row.append({"text": f"{status}{label}", "callback_data": f"toggle:{val}"})
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([{"text": "Next ➡️", "callback_data": "platform_next"}])
    return keyboard


def get_confirm_post_buttons(platforms: list) -> list:
    """Return inline keyboard buttons for confirming posts to Airtable/socials."""
    keyboard = []
    for plat in platforms:
        keyboard.append([
            {"text": f"✅ Confirm & Post {plat.upper()}", "callback_data": f"confirm_platform:{plat}"}
        ])
    return keyboard
