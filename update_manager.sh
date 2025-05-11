#!/bin/bash

# Navigiere zum Projektverzeichnis
cd "$(dirname "$0")"

# Pull neueste Änderungen von Git
echo "Pulling latest changes from Git..."
git pull

# Aktualisiere die virtuelle Umgebung
echo "Updating dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "Virtual environment not found at 'venv'. Please create it with: python -m venv venv"
    exit 1
fi

# Neustart des Servers - OS-spezifisch
echo "Restarting server..."
if command -v systemctl &> /dev/null; then
    # Linux mit systemd
    systemctl --user restart buyhigh
elif [ "$(uname)" == "Darwin" ]; then
    # macOS
    pkill -f gunicorn
    ./start_server.sh &
    echo "Server restarted on macOS"
else
    # Fallback für andere Systeme
    pkill -f gunicorn
    ./start_server.sh &
    echo "Server restarted"
fi

echo "Update completed!"
