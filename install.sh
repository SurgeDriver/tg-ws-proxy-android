#!/bin/bash
set -e

echo "Installing dependencies..."
pkg update -y
pkg install python git rust clang python-cryptography python-psutil python-pillow -y

rm -rf ~/tg-ws-proxy-android

echo "Cloning repository..."
git clone https://github.com/SurgeDriver/tg-ws-proxy-android.git ~/tg-ws-proxy-android

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
pip install -r ~/tg-ws-proxy-android/requirements.txt

echo "Installing tgproxy command..."
cat > "$PREFIX/bin/tgproxy" << SCRIPT
#!/bin/bash
exec python ~/tg-ws-proxy-android/android.py "\$@"
SCRIPT
chmod +x "$PREFIX/bin/tgproxy"

echo ""
echo "Done! Run: tgproxy"
echo ""
echo "Acquiring Wake Lock (keeps Android from sleeping)..."
termux-wake-lock

tgproxy
