# Dynamic Multi-Tier Model Router (TanAir)

Gunakan modul ini untuk menentukan penyedia LLM (*model provider*) mengikut konfigurasi tunggal di `~/.hermes/config.yaml`.

---

## 🔀 LOGIK PENGHALAAN PINTAR (CANONICAL MODEL ROUTING)

```text
               ┌───────────────────────┐
               │    Permintaan Boss    │
               └───────────┬───────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
  [💬 Teks & Kod]    [🛡️ Fallback API]   [📸 Imej & Fail]
       │                   │                   │
  🥇 BytePlus          🇨🇳 zAI (GLM-4)        🔮 Gemini
(ModelArk Coding)    (Primary Fallback)   (Multimodal/2M)
```

1. **🥇 BytePlus ModelArk Coding Plan (`custom:byteplus` / `ark-code-latest`) ➔ Model Teras / Primary Engine**:
   * Sembang harian, koding (`deepseek-v4-pro-ga-260813`), penulisan draf (`deepseek-v4-flash-ga-260731`), analisa pantas (`glm-5.3-flash-260828`), dan penaakulan logik.

2. **🇨🇳 zAI GLM-4 (`ZAI_API_KEY` / `GLM_API_KEY`) ➔ Model Sandaran Utama (Primary Fallback)**:
   * Fallback automatik sekiranya enjin utama mengalami masalah, analisis data berstruktur, dan pemprosesan artikel dwibahasa.
3. **🔮 Google Gemini (`GEMINI_API_KEY`) ➔ Multimodal & Fail Panjang**:
   * Analisis tangkap layar skrin (screenshot carta), fail PDF tebal, dokumen bersaiz besar (> 100K token).

