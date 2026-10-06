#!/bin/bash
# ==============================================================================
# SmartTask AI — 1-Buyruqda Serverga O'rnatish (One-liner installer)
# Ishlatish: curl -sSL https://raw.githubusercontent.com/qarshiyevziyodulla35-netizen/smart-task-ai/main/deploy/install.sh | bash
# ==============================================================================
set -e

echo "=================================================================="
echo "🚀 SmartTask AI — Serverga O'rnatish Boshlanmoqda..."
echo "=================================================================="

# Root huquqini tekshirish
if [ "$EUID" -ne 0 ]; then
  echo "❌ Iltimos, ushbu skriptni root sifatida ishga tushiring: sudo bash"
  exit 1
fi

apt-get update && apt-get install -y git curl

INSTALL_DIR="/opt/smarttask_ai"
if [ -d "$INSTALL_DIR" ]; then
    echo "🔄 Mavjud papka yangilanmoqda..."
    cd "$INSTALL_DIR"
    git pull || (cd / && rm -rf "$INSTALL_DIR" && git clone https://github.com/qarshiyevziyodulla35-netizen/smart-task-ai.git "$INSTALL_DIR")
else
    echo "📥 GitHub-dan yuklab olinmoqda..."
    git clone https://github.com/qarshiyevziyodulla35-netizen/smart-task-ai.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
chmod +x deploy/deploy_vps.sh
bash deploy/deploy_vps.sh
