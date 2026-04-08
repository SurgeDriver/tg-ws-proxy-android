#!/bin/bash
set -e

echo "Installing dependencies..."
pkg update -y
pkg install python git rust clang python-cryptography python-psutil python-pillow -y

rm -rf ~/tg-ws-proxy-android

echo "Cloning repository..."
git clone https://github.com/SurgeDriver/tg-ws-proxy-android.git ~/tg-ws-proxy-android

echo "Generating credentials and port..."
USERNAME=$(cat /dev/urandom | tr -dc 'a-z0-9' | head -c 16)
PASSWORD=$(cat /dev/urandom | tr -dc 'a-z0-9' | head -c 24)
# Pick a random port in the non-well-known, non-registered range: 32768-60999
PORT=$(( ( $(od -An -N2 -tu2 /dev/urandom | tr -d ' ') % 28232 ) + 32768 ))

echo "Creating config file..."
mkdir -p ~/TgWsProxy
cat > ~/TgWsProxy/config.json << EOF
{
  "port": $PORT,
  "host": "127.0.0.1",
  "dc_ip": [
    "2:149.154.167.220",
    "3:149.154.175.100",
    "4:149.154.167.220",
    "5:91.108.56.190"
  ],
  "verbose": false,
  "username": "$USERNAME",
  "password": "$PASSWORD",
  "no_auth": false
}
EOF

echo ""
echo "====================================="
echo " Telegram proxy settings (save these)"
echo "====================================="
echo " Host:     127.0.0.1"
echo " Port:     $PORT"
echo " Username: $USERNAME"
echo " Password: $PASSWORD"
echo "====================================="
echo ""

echo "Installing Python requirements..."
pip install -r ~/tg-ws-proxy-android/requirements.txt

echo "Installing tgproxy command..."
cat > "$PREFIX/bin/tgproxy" << SCRIPT
#!/bin/bash
exec python ~/tg-ws-proxy-android/android.py "\$@"
SCRIPT
chmod +x "$PREFIX/bin/tgproxy"

echo "Done! Run: tgproxy"
echo ""
echo "Acquiring Wake Lock (keeps Android from sleeping)..."
termux-wake-lock

tgproxy
