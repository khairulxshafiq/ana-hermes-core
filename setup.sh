#!/usr/bin/env bash
# ==============================================================================
# ANA-HERMES-CORE — Automated Turn-key Setup Script
# ==============================================================================
set -euo pipefail

echo "======================================================"
echo "🚀 Memulakan Pemasangan ANA Hermes Core..."
echo "======================================================"

# 1. Pastikan persekitaran Linux Ubuntu / Debian
if ! command -v curl &> /dev/null; then
    echo "📦 Memasang dependencies asas (curl, git, python3, build-essential)..."
    sudo apt-get update && sudo apt-get install -y curl git python3 python3-pip python3-venv build-essential
fi

HERMES_DIR="$HOME/.hermes"
mkdir -p "$HERMES_DIR"
mkdir -p "$HERMES_DIR/agents"
mkdir -p "$HERMES_DIR/skills"

# 2. Pasang Hermes Agent Runtime jika belum ada
if ! command -v hermes &> /dev/null; then
    echo "📥 Memasang Hermes Agent CLI..."
    curl -fsSL https://raw.githubusercontent.com/NousResearch/Hermes-Agent/main/scripts/install.sh | bash || true
fi

# 3. Salin Konfigurasi & Persona Watak
echo "⚙️  Menyusun konfigurasi dan persona watak..."
cp -r personas/* "$HERMES_DIR/agents/" 2>/dev/null || true
cp -r skills/* "$HERMES_DIR/skills/" 2>/dev/null || true

# Salin config.yaml jika belum wujud
if [ ! -f "$HERMES_DIR/config.yaml" ]; then
    echo "📄 Menyalin config.template.yaml ke ~/.hermes/config.yaml..."
    cp config/config.template.yaml "$HERMES_DIR/config.yaml"
fi

# Salin SOUL.md lalai jika ada
if [ -f "personas/SOUL_default_ana_chief_of_staff.md" ]; then
    cp "personas/SOUL_default_ana_chief_of_staff.md" "$HERMES_DIR/SOUL.md"
fi

# 4. Semak Fail .env
if [ ! -f "$HERMES_DIR/.env" ]; then
    if [ -f ".env" ]; then
        cp .env "$HERMES_DIR/.env"
        echo "✅ Fail .env disalin ke ~/.hermes/.env"
    else
        cp .env.example "$HERMES_DIR/.env"
        echo "⚠️  PERHATIAN: Sila edit ~/.hermes/.env dan masukkan API Keys anda:"
        echo "   nano ~/.hermes/.env"
    fi
fi

# 5. Pasang Systemd User Service (Opsional / Automatik)
echo "🔧 Memasang Systemd service..."
mkdir -p "$HOME/.config/systemd/user/"
cp systemd/hermes-gateway.service "$HOME/.config/systemd/user/"
systemctl --user daemon-reload || true

echo ""
echo "======================================================"
echo "🎉 Pemasangan Selesai!"
echo "======================================================"
echo "Langkah seterusnya:"
echo "1. Pastikan API Keys anda telah diisi:"
echo "   nano ~/.hermes/.env"
echo ""
echo "2. Uji cuba jalan Hermes Gateway:"
echo "   hermes gateway run"
echo ""
echo "3. Atau aktifkan sebagai latar belakang 24/7 (systemd):"
echo "   systemctl --user enable --now hermes-gateway"
echo "======================================================"
