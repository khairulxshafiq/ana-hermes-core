---
name: replicate-lora
description: "Pakej, muat naik, dan latih model LoRA (FLUX / SDXL) di Replicate secara async dengan pengesahan URL dan pengesanan status berkekalan."
version: 1.0.0
author: TanAir AI / ANA MLOps
license: MIT
tags: [replicate, lora, flux, fine-tuning, training, mlops]
platforms: [linux, macos]
---

# Replicate LoRA Training Skill (`replicate-lora`)

Modul ini mengautomasikan kitaran penuh latihan LoRA model AI (seperti FLUX.1 [dev] atau SDXL) di Replicate secara tak segerak (async) tanpa risiko kegagalan pautan tamat tempoh (*expired URL*).

Direka khas untuk Hermes Agent / ANA.ai supaya tiada lagi masalah kegagalan tersembunyi atau skrip ad-hoc dalam sesi perbualan.

---

## 🛠️ Perintah Utama (`scripts/lora_manager.py`)

Skrip pengurusan terletak di:
`~/.hermes/skills/mlops/replicate-lora/scripts/lora_manager.py`

### 1. Pakej Imej Menjadi Zip Bersih
Mengimbas folder imej, menapis artifak sistem (`.DS_Store`, `__MACOSX`), menyertakan fail kapsyen (`.txt`), dan memampatkan ke dalam fail zip yang serasi.
```bash
python3 ~/.hermes/skills/mlops/replicate-lora/scripts/lora_manager.py prepare <FOLDER_IMEJ> [--out dataset.zip]
```

### 2. Muat Naik ke Storan Tahan Lama (>=4 Jam)
Memuat naik fail zip ke Google Drive (menggunakan kebenaran `google_token.json` dengan akses awam) atau pelayan staging berdaya tahan (`tmpfiles.org`), kemudian **mengesahkan serta-merta** melalui semakan `HTTP GET 200` sebelum mengembalikan pautan muat turun langsung.
```bash
python3 ~/.hermes/skills/mlops/replicate-lora/scripts/lora_manager.py upload dataset.zip [--method auto|drive|temp]
```

### 3. Mulakan Latihan Asynchronous di Replicate
Menghantar permintaan latihan ke Replicate API. Metadata dan status awal disimpan terus ke fail berterusan `~/.hermes/lora_tasks.json`.
```bash
python3 ~/.hermes/skills/mlops/replicate-lora/scripts/lora_manager.py train \
  --dataset-url "<VERIFIED_DOWNLOAD_URL>" \
  --destination "<USERNAME/MODEL_NAME>" \
  --trigger-word "<TRIGGER_WORD>" \
  --steps 1000
```

### 4. Semak Status & Pengesanan Ralat Segera
Menyemak status semasa latihan daripada Replicate, mengemaskini `~/.hermes/lora_tasks.json`, dan mengekstrak ralat secara terperinci jika terdapat kegagalan.
```bash
python3 ~/.hermes/skills/mlops/replicate-lora/scripts/lora_manager.py status <TRAINING_ID>
```

### 5. Senarai Semua Tugasan Latihan
Memaparkan jadual semua latihan LoRA yang pernah dijalankan beserta status terkini.
```bash
python3 ~/.hermes/skills/mlops/replicate-lora/scripts/lora_manager.py list
```

---

## 🛡️ Protokol Pelaksanaan untuk ANA.ai
1. **Dilarang Menulis Skrip Mentah Dalam Sembang:** Sentiasa panggil CLI `lora_manager.py`.
2. **Pengesahan Pautan Sebelum Training:** Skrip secara automatik menghalang latihan dihantar jika pautan tidak memulangkan status `HTTP 200`.
3. **Makluman <60 Saat:** Sebaik sahaja `train` dijalankan, segera kemukakan `Training ID` dan pautan papan pemuka Replicate kepada pengguna. Jika status bertukar kepada `failed`, laporkan ralat sebenar serta-merta!

