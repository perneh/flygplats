#!/usr/bin/env bash
# Packer shell provisioner (runs as sudo via Packer). Installs XFCE + X11 + frontend deps.
set -euo pipefail

if [[ -f /tmp/start-x11.sh ]]; then
  install -m 755 /tmp/start-x11.sh /usr/local/bin/start-x11.sh
fi
if [[ -f /tmp/run-frontend.sh ]]; then
  install -m 755 /tmp/run-frontend.sh /usr/local/bin/run-frontend.sh
fi

INSTALL="${FRONTEND_INSTALL_DIR:-/opt/flygplats}"
SRC_TYPE="${FRONTEND_SOURCE_TYPE:-git}"
GIT_URL="${FRONTEND_GIT_URL:-}"
GIT_REF="${FRONTEND_GIT_REF:-main}"
DW="${DISPLAY_WIDTH:-1280}"
DH="${DISPLAY_HEIGHT:-800}"

if [[ "$SRC_TYPE" == "git" && -z "$GIT_URL" ]]; then
  echo "FRONTEND_GIT_URL is empty. Set frontend_git_url in your var-file" >&2
  echo "or run with PKR_VAR_frontend_git_url explicitly set." >&2
  exit 2
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends \
  ca-certificates curl git \
  xfce4 xfce4-goodies lightdm lightdm-gtk-greeter \
  dbus-x11 xserver-xorg x11-xserver-utils x11-apps x11-utils xdotool \
  python3 python3-venv python3-pip \
  unzip tar \
  openssh-server

# X11 only — do not install gdm3 (Wayland default on some stacks).
systemctl set-default graphical.target

mkdir -p /etc/lightdm/lightdm.conf.d
cat >/etc/lightdm/lightdm.conf.d/50-autologin.conf <<'EOF'
[Seat:*]
autologin-user=debian
autologin-user-timeout=0
autologin-session=xfce
user-session=xfce
EOF

cat >/etc/lightdm/lightdm.conf.d/70-x11-listen-tcp.conf <<'EOF'
[Seat:*]
# +listen tcp exposes X on port 6000+d for remote clients (firewall / xhost still required).
xserver-command=X -core -noreset +listen tcp -dpi 96
EOF

mkdir -p /etc/golf-gui
cat >/etc/golf-gui/x11-host-allow <<'EOF'
# Optional: one rule per line for xhost (examples — edit after deploy):
# inet:10.0.0.5
# inet:172.17.0.0
EOF

cat >/etc/systemd/system/golf-x11-acl.service <<'EOF'
[Unit]
Description=Apply X11 xhost rules for remote automation
After=display-manager.service
PartOf=graphical.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/start-x11.sh
RemainAfterExit=yes

[Install]
WantedBy=graphical.target
EOF

systemctl enable golf-x11-acl.service

cat >/usr/local/bin/golf-desktop-autostart.sh <<'EOF'
#!/usr/bin/env bash
# Start Golf Desktop once per graphical login (XFCE autostart).
set -euo pipefail
export DISPLAY="${DISPLAY:-:0}"
export GDK_BACKEND="${GDK_BACKEND:-x11}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"

if pgrep -u "$(id -un)" -f "python.*-m golf_desktop" >/dev/null 2>&1; then
  exit 0
fi

# Give LightDM/XFCE a moment to finish session setup.
sleep 3
exec /usr/local/bin/run-frontend.sh
EOF
chmod 755 /usr/local/bin/golf-desktop-autostart.sh

# Per-user autostart (runs after autologin to XFCE).
install -d -o debian -g debian -m 755 /home/debian/.config/autostart
cat >/home/debian/.config/autostart/golf-desktop.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Golf Desktop (autostart)
Comment=Start golf desktop after XFCE login
Exec=/usr/local/bin/golf-desktop-autostart.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
chown debian:debian /home/debian/.config/autostart/golf-desktop.desktop
chmod 644 /home/debian/.config/autostart/golf-desktop.desktop

# Reduce blanking / lock surprises in automated GUI tests
mkdir -p /etc/xdg/autostart
cat >/etc/xdg/autostart/golf-xfce-power.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Golf GUI test power tweaks
Exec=sh -c "xset s off; xset -dpms; xset s noblank || true"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

mkdir -p "$INSTALL"
if [[ "$SRC_TYPE" == "git" ]]; then
  rm -rf "$INSTALL/repo"
  git clone "$GIT_URL" "$INSTALL/repo"
  git -C "$INSTALL/repo" checkout "$GIT_REF"
  FRONTEND_ROOT="$INSTALL/repo"
else
  echo "artifact mode: place tarball at /tmp/frontend-artifact.tgz before provisioning" >&2
  if [[ -f /tmp/frontend-artifact.tgz ]]; then
    mkdir -p "$INSTALL/artifact"
    tar -xzf /tmp/frontend-artifact.tgz -C "$INSTALL/artifact"
    FRONTEND_ROOT="$INSTALL/artifact"
  else
    FRONTEND_ROOT="$INSTALL"
  fi
fi

python3 -m venv /opt/golf-venv
/opt/golf-venv/bin/pip install --upgrade pip
if [[ -f "$FRONTEND_ROOT/frontend/requirements-core.txt" ]]; then
  /opt/golf-venv/bin/pip install -r "$FRONTEND_ROOT/frontend/requirements-core.txt"
elif [[ -f "$FRONTEND_ROOT/requirements-core.txt" ]]; then
  /opt/golf-venv/bin/pip install -r "$FRONTEND_ROOT/requirements-core.txt"
else
  echo "Could not find requirements-core.txt under $FRONTEND_ROOT" >&2
  exit 1
fi

cat >/etc/golf-gui/env <<EOF
FRONTEND_ROOT=$FRONTEND_ROOT
FRONTEND_VENV=/opt/golf-venv
API_BASE_URL=http://host.docker.internal:8000
DISPLAY_WIDTH=$DW
DISPLAY_HEIGHT=$DH
EOF
chmod 644 /etc/golf-gui/env

systemctl enable lightdm
echo "Provisioning complete. Reboot recommended before first GUI capture."
