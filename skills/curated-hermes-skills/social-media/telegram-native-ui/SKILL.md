# Telegram Native UI & Interactive Keyboard (TanAir)

Gunakan modul ini untuk menghasilkan papan kekunci interaktif (*Inline Keyboard Markup*) apabila berinteraksi dengan pengguna di Telegram.

---

## 📱 TEMPLAT PAPAN KEKUNCI INTERAKTIF (INLINE BUTTONS)

### 1. 🔗 Apabila Pengguna Berkongsi Pautan (URL Flow):
```json
{
  "inline_keyboard": [
    [
      {"text": "📰 Scrape Jadi FB Post", "callback_data": "scrape_fb"},
      {"text": "🧵 Buat Thread X", "callback_data": "scrape_x"}
    ],
    [
      {"text": "🔍 Ringkasan Pantas", "callback_data": "scrape_summary"},
      {"text": "💬 Sembang Santai", "callback_data": "scrape_chat"}
    ]
  ]
}
```

### 2. 📊 Apabila Menganalisis Saham / Kripto:
```json
{
  "inline_keyboard": [
    [
      {"text": "🎯 Trade Plan (Swing)", "callback_data": "trade_swing"},
      {"text": "🏦 ASB/DCA (Position)", "callback_data": "trade_position"}
    ],
    [
      {"text": "🩺 Semak Status FA", "callback_data": "check_fa"},
      {"text": "🔔 Tambah Watchlist", "callback_data": "add_watchlist"}
    ]
  ]
}
```
