#!/bin/bash
set -e

echo "Installing dependencies..."
pkg update -y
pkg install python git rust clang python-cryptography python-psutil python-pillow -y

rm -rf tg-ws-proxy-android

echo "Cloning repository..."
git clone https://github.com/SurgeDriver/tg-ws-proxy-android.git
cd tg-ws-proxy-android

echo "Creating config file..."
mkdir -p ~/TgWsProxy
cat << 'EOF' > ~/TgWsProxy/config.json
{
  "port": 1080,
  "host": "127.0.0.1",
  "dc_ip": [
    "2:149.154.167.220",
    "3:149.154.175.100",
    "4:149.154.167.220",
    "5:91.108.56.190"
  ],
  "verbose": false
}
EOF

echo "Installing Python requirements..."
pip install -r requirements.txt

# --- alias setup ---
INSTALL_DIR="$(pwd)"
ALIAS_LINE="alias tgproxy='python ${INSTALL_DIR}/android.py'"

# Detect shell rc file
if [ -n "$ZSH_VERSION" ] || [ "$(basename "$SHELL")" = "zsh" ]; then
    RC_FILE="$HOME/.zshrc"
else
    RC_FILE="$HOME/.bashrc"
fi

# Add alias only if not already present
if ! grep -qF "alias tgproxy=" "$RC_FILE" 2>/dev/null; then
    echo "" >> "$RC_FILE"
    echo "# tg-ws-proxy-android" >> "$RC_FILE"
    echo "$ALIAS_LINE" >> "$RC_FILE"
    echo "Alias 'tgproxy' added to $RC_FILE"
else
    echo "Alias 'tgproxy' already exists in $RC_FILE, skipping."
fi
# -------------------

echo "Setup complete!"
echo "Run: source $RC_FILE  (or restart Termux session)"
echo "Then: tgproxy"
echo ""
echo "Acquiring Wake Lock (keeps Android from sleeping)..."
termux-wake-lock

echo "Starting Proxy..."
python android.py
