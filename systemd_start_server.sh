#!/bin/bash
# filepath: /Users/julianstosse/Developer/BuyHigh.io/setup_user_systemd_service.sh

SERVICE_NAME=buyhigh
WORKING_DIR="$(cd "$(dirname "$0")"; pwd)"
START_SCRIPT="$WORKING_DIR/start_server.sh"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SYSTEMD_USER_DIR/${SERVICE_NAME}.service"

mkdir -p "$SYSTEMD_USER_DIR"

cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=BuyHigh.io App

[Service]
Type=simple
WorkingDirectory=$WORKING_DIR
ExecStart=$START_SCRIPT
Restart=always

[Install]
WantedBy=default.target
EOL

systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME"

echo "User-Systemd-Service '$SERVICE_NAME' wurde eingerichtet und gestartet."
echo "Status prüfen mit: systemctl --user status $SERVICE_NAME"