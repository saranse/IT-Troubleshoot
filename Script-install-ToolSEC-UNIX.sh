 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/security_toolkit.sh b/security_toolkit.sh
new file mode 100644
index 0000000000000000000000000000000000000000..4d187a5ed2277800cc9313bb95847704f91d79d2
--- /dev/null
+++ b/security_toolkit.sh
@@ -0,0 +1,996 @@
+#!/bin/bash
+
+#=================== VERSION AND UPDATE ===================
+SCRIPT_VERSION="1.5"
+UPDATE_URL="http://203.151.249.125/index.php/s/j3AbGFrecydMr6W/download"
+VERSION_URL="http://203.151.249.125/index.php/s/iD8ig6tb8Zro3Bo/download"
+LOCAL_PATH="$(realpath "$0")"
+
+#------------------- AUTO UPDATE -------------------
+auto_update() {
+  echo -n "🔍 Checking for updates... "
+  if ! command -v curl >/dev/null 2>&1; then
+    echo "⚠️  curl not found. Attempting to install..."
+    if [ -f /etc/redhat-release ]; then
+      yum install -y curl >/dev/null 2>&1
+    elif [ -f /etc/debian_version ]; then
+      apt-get update -qq >/dev/null 2>&1
+      apt-get install -y curl >/dev/null 2>&1
+    else
+      echo "❌ Cannot install curl. Unknown OS."
+      return
+    fi
+  fi
+  REMOTE_VERSION=$(curl -s --max-time 5 "$VERSION_URL")
+  if [ -z "$REMOTE_VERSION" ]; then
+    echo "❌ Failed to check version (timeout or unreachable)"
+    echo "🚧 Continuing with local version $SCRIPT_VERSION"
+    return
+  fi
+  if [ "$REMOTE_VERSION" != "$SCRIPT_VERSION" ]; then
+    echo "⬆️  Updating to version $REMOTE_VERSION..."
+    curl -s --max-time 10 -o /tmp/latest.sh "$UPDATE_URL"
+    if [ $? -eq 0 ]; then
+      cp /tmp/latest.sh "$LOCAL_PATH"
+      chmod +x "$LOCAL_PATH"
+      echo "✅ Update complete. Restarting..."
+      exec "$LOCAL_PATH"
+    else
+      echo "❌ Download failed. Continue using current version."
+    fi
+  else
+    echo "🆗 Already at latest version ($SCRIPT_VERSION)"
+  fi
+}
+
+#------------------- ENSURE clear INSTALLED -------------------
+ensure_clear_installed() {
+  if ! command -v clear &>/dev/null; then
+    echo "🔧 'clear' command not found. Installing..."
+    if [ -f /etc/redhat-release ]; then
+      yum install -y ncurses >/dev/null 2>&1
+    elif [ -f /etc/debian_version ]; then
+      apt-get update >/dev/null 2>&1
+      apt-get install -y ncurses-bin >/dev/null 2>&1
+    else
+      echo "❌ Unsupported OS. Please install 'clear' manually."
+      return 1
+    fi
+    if command -v clear &>/dev/null; then
+      echo "✅ 'clear' installed successfully."
+    else
+      echo "❌ Failed to install 'clear'. Proceeding without it."
+    fi
+  fi
+}
+
+#=================== HELPER FUNCTIONS ===================
+print_status() {
+  local label="$1"
+  local status="$2"
+  if [ "$status" == "OK" ]; then
+    echo -e "✅ \e[1;32m$label\e[0m"
+  else
+    echo -e "⚠️  Failed \e[1;31m$label\e[0m"
+  fi
+}
+
+print_red()     { echo -e "\e[1;31m$1\e[0m"; }
+print_green()   { echo -e "\e[1;32m$1\e[0m"; }
+print_yellow()  { echo -e "\e[1;33m$1\e[0m"; }
+print_blue()    { echo -e "\e[1;34m$1\e[0m"; }
+print_purple()  { echo -e "\e[1;35m$1\e[0m"; }
+print_cyan()    { echo -e "\e[1;36m$1\e[0m"; }
+print_white()   { echo -e "\e[1;37m$1\e[0m"; }
+
+show_loading_animation() {
+  local chars='|/-\\'
+  local delay=0.1
+  local duration=$1
+  local end_time=$((SECONDS + duration))
+  while [ $SECONDS -lt $end_time ]; do
+    for ((i=0; i<${#chars}; i++)); do
+      printf "\r%s" "${chars:$i:1}"
+      sleep $delay
+    done
+  done
+  printf "\r"
+}
+
+show_progress_bar() {
+  local total=50
+  local duration=$1
+  local increment=$((duration * 10 / total))
+  for ((i = 1; i <= total; i++)); do
+    local percent=$(( i * 100 / total ))
+    local bar=$(printf "%-${total}s" "=" | sed "s/ /=/g")
+    bar="${bar:0:i}>"
+    printf "\r%3d%%[%-${total}s]" "$percent" "$bar"
+    sleep 0.$((increment * 10))
+  done
+  printf "\n"
+}
+
+#=================== CONNECTIVITY CHECK ===================
+detect_os() {
+  if [ -f /etc/redhat-release ]; then
+    OS="Red Hat-Based"
+    INSTALL_COMMAND="yum install -y"
+  elif [ -f /etc/debian_version ]; then
+    OS="Debian-Based"
+    INSTALL_COMMAND="apt-get install -y"
+  else
+    OS="Unsupported"
+  fi
+}
+
+ensure_nc_installed() {
+  if ! command -v nc >/dev/null 2>&1; then
+    echo -e "\n🧰 Installing 'nc' (netcat)..."
+    detect_os
+    if [[ "$OS" == "Debian-Based" ]]; then
+      apt-get update -qq && apt-get install -y netcat >/dev/null 2>&1
+    elif [[ "$OS" == "Red Hat-Based" ]]; then
+      yum install -y nc >/dev/null 2>&1
+    else
+      echo "❌ Unsupported OS for installing nc"
+      return 1
+    fi
+  fi
+}
+
+test_connectivity() {
+  local host=$1
+  local port=$2
+  timeout 3 nc -z -w 2 "$host" "$port" >/dev/null 2>&1
+  [ $? -eq 0 ] && echo "OK" || echo "FAIL"
+}
+
+check_connectivity_status() {
+  echo -e "\e[5;97;41m🌐 CONNECTIVITY STATUS CHECK\e[0m"
+  echo "------------------------------------------------------------------"
+  ensure_nc_installed || return 1
+  declare -A targets=(
+    ["Connect to Crowdstrike [EDR]    : edr-proxy.inet.co.th"]="edr-proxy.inet.co.th:3128"
+    ["Connect to SentinelOne [S1]     : apse1-2002.sentinelone.net"]="apse1-2002.sentinelone.net:443"
+    ["Connect to DUO Security         : api-707328e5.duosecurity.com"]="api-707328e5.duosecurity.com:443"
+    ["Connect to FortiSIEM Proxy      : siem-proxy.inet.co.th"]="siem-proxy.inet.co.th:443"
+    ["Connect to FortiSIEM Supervisor : siem-supervisor.inet.co.th"]="siem-supervisor.inet.co.th:443"
+    ["Connect to FortiSIEM WorkerData : siem-workerdata.inet.co.th"]="siem-workerdata.inet.co.th:443"
+  )
+  for label in "${!targets[@]}"; do
+    IFS=':' read -r host port <<< "${targets[$label]}"
+    result=$(test_connectivity "$host" "$port")
+    print_status "$label" "$result"
+    sleep 0.2
+  done
+  echo ""
+}
+
+# === TELEGRAM CONFIG ===
+TELEGRAM_BOT_TOKEN="7513451139:AAH1PEHjQS4_y0N2YWCT4Lf0C9hVCybprO0"
+TELEGRAM_CHAT_ID="-1002605135756"
+
+#=================== DUO SECURITY UTILITIES ===================
+duo_logo() {
+  local logo=(
+"▗▄▄▄ ▗▖ ▗▖ ▗▄▖      ▗▄▄▖▗▄▄▄▖ ▗▄▄▖▗▄▄▄▖▗▖  ▗▖▗▄▄▄▖▗▄▄▄▖"
+"▐▌  █▐▌ ▐▌▐▌ ▐▌    ▐▌   ▐▌   ▐▌     █  ▐▛▚▖▐▌▐▌     █   "
+"▐▌  █▐▌ ▐▌▐▌ ▐▌     ▝▀▚▖▐▛▀▀▘▐▌     █  ▐▌ ▝▜▌▐▛▀▀▘  █   "
+"▐▙▄▄▀▝▚▄▞▘▝▚▄▞▘    ▗▄▄▞▘▐▙▄▄▖▝▚▄▄▖▗▄█▄▖▐▌  ▐▌▐▙▄▄▖  █   "
+"                                                        "
+"        [ 🔐 SECURE AUTHENTICATION INSTALLER 🔐  ]       "
+  )
+  local bar="------------------------------------------------------------"
+  local color=32
+  clear
+  echo ""
+  for line in "${logo[@]}"; do
+    echo -e "\e[1;${color}m${line}\e[0m"
+  done
+  echo ""
+  echo -e "\e[1;${color}m${bar}\e[0m"
+  echo ""
+  show_os_info
+  check_internet
+  review_user_accounts
+}
+
+check_internet() {
+  if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
+    printf "Internet   : "; slow_print "✅  Connected"
+  else
+    printf "Internet   : "; print_red "❌  No Connection"
+  fi
+  if ping -c 1 -W 2 google.com > /dev/null 2>&1; then
+    printf "DNS Resolve: "; slow_print "✅  Working"
+  else
+    printf "DNS Resolve: "; print_red "❌  Failed"
+  fi
+}
+
+check_internet_install_duo() {
+  echo "Checking internet connection..."
+  echo "Check 1: Testing internet connectivity with ping..."
+  if ping -c 1 www.google.com > /dev/null 2>&1; then
+    echo "Check 1 passed: Internet is connected (via ping)."
+    echo "Checking connectivity to port 80..."
+    if nc -z -w 5 www.google.com 443 > /dev/null 2>&1; then
+      echo "Port 80 is reachable."
+    else
+      echo -e "\033[0;31mPort 80 is not reachable\033[0m"
+    fi
+    echo "Checking connectivity to port 443..."
+    if nc -z -w 5 www.google.com 80 > /dev/null 2>&1; then
+      echo "Port 443 is reachable."
+    else
+      echo -e "\033[0;31mPort 443 is not reachable\033[0m"
+    fi
+    run_install_duo
+    return
+  else
+    echo -e "\033[0;31mCheck 1 failed: Internet connectivity unsuccessful (via ping)\033[0m"
+  fi
+  echo "Check 2: Testing with curl to Google..."
+  if curl -s --head http://www.google.com | head -n 1 | grep "HTTP/1.[01] [23].." > /dev/null; then
+    echo "Check 2 passed: Internet is connected (via curl)."
+    run_install_duo
+    return
+  else
+    echo -e "\033[0;31mCheck 2 failed: Unable to connect via curl\033[0m"
+  fi
+  echo "Check 3: Testing with wget to Google..."
+  if wget --spider -q http://www.google.com; then
+    echo "Check 3 passed: Internet is connected (via wget)."
+    run_install_duo
+    return
+  else
+    echo -e "\033[0;31mCheck 3 failed: Unable to connect via wget\033[0m"
+  fi
+  echo -e "\033[0;31mAll internet checks failed.\033[0m"
+  while true; do
+    read -p "Do you want to bypass the internet check and continue? (Y/n): " choice
+    case "$choice" in
+      [Yy]* )
+        echo "Bypassing internet check and proceeding with installation..."
+        run_install_duo
+        return
+        ;;
+      [Nn]* )
+        echo "Exiting to main menu. Please check your internet connection."
+        main_menu
+        return
+        ;;
+      * ) echo "Please answer Y (yes) or N (no).";;
+    esac
+  done
+}
+
+run_install_duo() {
+  show_loading_animation 3
+  echo "----------------------------------"
+  check_tools_and_install
+  if [ "$INSTALLATION_OCCURRED" = true ]; then
+    print_yellow "Some Tools were missing. Skipping Duo installation for now."
+  else
+    print_yellow "Installing Duo..."
+    show_loading_animation 5
+    echo "----------------------------------"
+    install_duo
+  fi
+}
+
+install_duo() {
+  echo "Downloading Duo Unix version $SELECTED_VERSION..."
+  wget --content-disposition "https://dl.duosecurity.com/$SELECTED_VERSION" -O "$SELECTED_VERSION"
+  if [ $? -ne 0 ]; then
+    print_red "Failed to download Duo Unix. Exiting..."
+  fi
+  echo "Extracting Duo Unix..."
+  tar -xzvf "$SELECTED_VERSION"
+  if [ $? -ne 0 ]; then
+    print_red "Failed to extract $SELECTED_VERSION"
+  fi
+  DUO_DIR=$(tar -tzf "$SELECTED_VERSION" | head -1 | cut -f1 -d"/")
+  if [ -z "$DUO_DIR" ]; then
+    print_red "Failed to determine Duo Unix directory. Exiting..."
+  fi
+  echo "Changing directory to $DUO_DIR..."
+  cd "$DUO_DIR" || return
+  if [ -f /etc/duo/login_duo.conf ] || [ -f /etc/login_duo.conf ]; then
+    print_green "Duo Unix is already configured."
+    echo "Configuring Duo Unix..."
+    if [ -f /etc/duo/login_duo.conf ]; then
+      echo "Found login_duo.conf file."
+      if [ -x "$(command -v nano)" ]; then
+        nano /etc/duo/login_duo.conf
+      else
+        vi /etc/duo/login_duo.conf
+      fi
+    else
+      echo "Found login_duo.conf file in /etc."
+      if [ -x "$(command -v nano)" ]; then
+        nano /etc/login_duo.conf
+      else
+        vi /etc/login_duo.conf
+      fi
+    fi
+    cd "$DUO_DIR"
+  else
+    echo "Installing Duo Unix..."
+    ./configure --prefix=/usr && make && sudo make install
+    if [ $? -ne 0 ]; then
+      print_red "Error during Duo Unix installation"
+    else
+      print_green "Duo Unix installed successfully."
+    fi
+    echo "Configuring Duo Unix..."
+    if [ -f /etc/duo/login_duo.conf ]; then
+      echo "Found login_duo.conf file."
+      if [ -x "$(command -v nano)" ]; then
+        nano /etc/duo/login_duo.conf
+      else
+        vi /etc/duo/login_duo.conf
+      fi
+    elif [ -f /etc/login_duo.conf ]; then
+      echo "Found login_duo.conf file in /etc."
+      if [ -x "$(command -v nano)" ]; then
+        nano /etc/login_duo.conf
+      else
+        vi /etc/login_duo.conf
+      fi
+    else
+      print_red "Error: login_duo.conf file not found in /etc/duo or /etc."
+    fi
+  fi
+  add_duo_config_to_sshd
+  clear
+  restart_ssh_service
+  send_telegram_alert
+}
+
+add_duo_config_to_sshd() {
+  local ssh_config="/etc/ssh/sshd_config"
+  local temp_file="/tmp/sshd_config.tmp"
+  if grep -q "ForceCommand /usr/sbin/login_duo" "$ssh_config"; then
+    print_yellow "Duo 2FA configuration already exists in $ssh_config"
+    return
+  fi
+  awk '
+  BEGIN { added=0 }
+  {
+    print
+    if (!added && $0 ~ /^#ListenAddress ::/) {
+      print ""
+      print "# Duo 2FA login"
+      print "ForceCommand /usr/sbin/login_duo"
+      print "PermitTunnel no"
+      print "AllowTcpForwarding no"
+      added=1
+    }
+  }' "$ssh_config" > "$temp_file" && mv "$temp_file" "$ssh_config"
+  chmod 600 "$ssh_config"
+  print_green "✅ Duo 2FA configuration added to $ssh_config"
+}
+
+uninstall_duo() {
+  if ! rpm -q duo_unix > /dev/null 2>&1; then
+    show_loading_animation 3
+    print_yellow "Duo Pam is already uninstalled."
+  else
+    show_loading_animation 3
+    print_yellow "Uninstalling Duo Pam..."
+    sudo yum remove duo_unix -y
+    print_green "Duo Unix package removed."
+  fi
+  if [ ! -d "/etc/duo" ] && [ ! -f "/etc/login_duo.conf" ] && [ ! -f "/usr/sbin/login_duo" ] && [ ! -f "/usr/lib/libduo.*" ] && [ ! -f "/etc/yum.repos.d/duosecurity.repo" ]; then
+    show_loading_animation 3
+    print_yellow "Duo files already removed."
+    skip_ssh_config=true
+  else
+    show_loading_animation 3
+    print_yellow "Removing Duo files..."
+    show_progress_bar 1
+    if [ -f "/etc/duo/login_duo.conf" ]; then
+      sudo rm -rf /etc/duo/login_duo.conf
+      print_green "Removed /etc/duo/login_duo.conf"
+    else
+      print_yellow "/etc/duo/login_duo.conf not found, skipping."
+    fi
+    if [ -f "/etc/login_duo.conf" ]; then
+      sudo rm -rf /etc/login_duo.conf
+      print_green "Removed /etc/login_duo.conf"
+    else
+      print_yellow "/etc/login_duo.conf not found, skipping."
+    fi
+    show_progress_bar 1
+    if [ -f "/usr/sbin/login_duo" ]; then
+      sudo rm -rf /usr/sbin/login_duo
+      print_green "Removed /usr/sbin/login_duo"
+    else
+      print_yellow "/usr/sbin/login_duo not found, skipping."
+    fi
+    show_progress_bar 1
+    if ls /usr/lib/libduo.* 1> /dev/null 2>&1; then
+      sudo rm -rf /usr/lib/libduo.*
+      print_green "Removed libduo.*"
+    else
+      print_yellow "libduo.* not found, skipping."
+    fi
+    show_progress_bar 1
+    if [ -f "/etc/yum.repos.d/duosecurity.repo" ]; then
+      sudo rm -rf /etc/yum.repos.d/duosecurity.repo
+      print_green "Removed duosecurity.repo"
+    else
+      print_yellow "duosecurity.repo not found, skipping."
+    fi
+    show_progress_bar 1
+    if [ -d "/etc/duo" ]; then
+      sudo rm -rf /etc/duo
+      print_green "Removed /etc/duo directory"
+    else
+      print_yellow "/etc/duo directory not found or not empty, skipping."
+    fi
+    show_progress_bar 3
+  fi
+  if [ -z "$skip_ssh_config" ]; then
+    echo "Editing SSH configuration..."
+    cd /etc/ssh
+    if [ -x "$(command -v nano)" ]; then
+      nano sshd_config
+    else
+      vi sshd_config
+    fi
+  fi
+  restart_ssh_service
+  print_green "Duo uninstallation completed."
+}
+
+#=================== PAM DUO INSTALL FUNCTIONS ===================
+check_os_version_pam_install() {
+  echo "Checking OS version, hostname, and IP address"
+  if [ -f /etc/os-release ]; then
+    . /etc/os-release
+    OS_INFO="$ID $VERSION_ID"
+  else
+    OS_INFO="Unable to detect OS: /etc/os-release not found."
+  fi
+  HOSTNAME=$(hostname 2>/dev/null || echo "Hostname command not found")
+  IP_ADDRESS=$(hostname -I | awk '{print $1}')
+  [ -z "$IP_ADDRESS" ] && IP_ADDRESS="IP Address not found"
+  print_green "OS version: $OS_INFO"
+  print_green "Hostname: $HOSTNAME"
+  print_green "IP Address: $IP_ADDRESS"
+  case "$ID" in
+    centos) OS_NAME="CentOS";;
+    fedora) OS_NAME="Fedora";;
+    centosstream) OS_NAME="CentOSStream";;
+    rhel) OS_NAME="RedHatEnterprise";;
+    *)
+      print_red "Not supported yet: $ID"
+      read -p "Press Enter to return to the menu..."
+      main_menu
+      ;;
+  esac
+  create_duo_repo "$OS_NAME"
+}
+
+create_duo_repo() {
+  local os="$1"
+  echo "Creating /etc/yum.repos.d/duosecurity.repo for Duo installation..."
+  cat <<EOF_REPO >/etc/yum.repos.d/duosecurity.repo
+[duosecurity]
+name=Duo Security Repository
+baseurl=http://pkg.duosecurity.com/${os}/\$releasever/\$basearch
+enabled=1
+gpgcheck=0
+EOF_REPO
+  install_duo_unix_pam
+}
+
+install_duo_unix_pam() {
+  print_green "Importing Duo GPG key and installing duo_unix..."
+  rpm --import https://duo.com/DUO-GPG-PUBLIC-KEY.asc
+  yum install duo_unix -y
+  configure_duo_unix_pam
+}
+
+configure_duo_unix_pam() {
+  echo "Configuring Duo Unix..."
+  if [ -f /etc/duo/pam_duo.conf ]; then
+    nano /etc/duo/pam_duo.conf
+  elif [ -f /etc/pam_duo.conf ]; then
+    nano /etc/pam_duo.conf
+  else
+    print_red "Error: pam_duo.conf file not found in /etc/duo or /etc."
+    exit 1
+  fi
+  show_duo_pam_config
+  echo "Editing SSH configuration..."
+  cd /etc/ssh
+  if [ -x "$(command -v nano)" ]; then
+    nano sshd_config
+  else
+    vi sshd_config
+  fi
+  clear
+  show_duo_pam_sshd_config
+  echo "Editing SSHD PAM configuration..."
+  cd /etc/pam.d
+  if [ -x "$(command -v nano)" ]; then
+    nano sshd
+  else
+    vi sshd
+  fi
+  clear
+  restart_ssh_service
+}
+
+show_duo_pam_sshd_config() {
+  clear
+  echo ""
+  echo "--------------------------------------------"
+  echo ""
+  echo -e "\e[38;2;0;255;0m\e[1m auth       required     pam_duo.so\e[0m"
+  echo ""
+  echo "--------------------------------------------"
+  echo "Please manually update the sshd_config as needed."
+  read -p "Press Enter to continue..."
+  clear
+}
+
+show_duo_pam_config() {
+  clear
+  echo ""
+  echo "--------------------------------------------"
+  echo ""
+  echo -e "\e[38;2;0;255;0m\e[1m ChallengeResponseAuthentication yes\e[0m"
+  echo ""
+  echo "--------------------------------------------"
+  echo "Please manually update the sshd_config as needed."
+  read -p "Press Enter to continue..."
+  clear
+}
+
+check_internet_install_duo_pam() {
+  echo "Checking internet connection..."
+  echo "Check 1: Testing internet connectivity with ping..."
+  if ping -c 1 www.google.com > /dev/null 2>&1; then
+    echo "Check 1 passed: Internet is connected (via ping)."
+    echo "Checking connectivity to port 80..."
+    if nc -z -w 5 www.google.com 80 > /dev/null 2>&1; then
+      echo "Port 80 is reachable."
+    else
+      echo -e "\033[0;31mPort 80 is not reachable\033[0m"
+    fi
+    echo "Checking connectivity to port 443..."
+    if nc -z -w 5 www.google.com 443 > /dev/null 2>&1; then
+      echo "Port 443 is reachable."
+    else
+      echo -e "\033[0;31mPort 443 is not reachable\033[0m"
+    fi
+    check_os_version_pam_install
+    return
+  else
+    echo -e "\033[0;31mCheck 1 failed: Internet connectivity unsuccessful (via ping)\033[0m"
+  fi
+  echo "Check 2: Testing with curl to Google..."
+  if curl -s --head http://www.google.com | head -n 1 | grep "HTTP/1.[01] [23].." > /dev/null; then
+    echo "Check 2 passed: Internet is connected (via curl)."
+    check_os_version_pam_install
+    return
+  else
+    echo -e "\033[0;31mCheck 2 failed: Unable to connect via curl\033[0m"
+  fi
+  echo "Check 3: Testing with wget to Google..."
+  if wget --spider -q http://www.google.com; then
+    echo "Check 3 passed: Internet is connected (via wget)."
+    check_os_version_pam_install
+    return
+  else
+    echo -e "\033[0;31mCheck 3 failed: Unable to connect via wget\033[0m"
+  fi
+  echo -e "\033[0;31mAll internet checks failed.\033[0m"
+  while true; do
+    read -p "Do you want to bypass the internet check and continue? (Y/n): " choice
+    case "$choice" in
+      [Yy]* )
+        echo "Bypassing internet check and proceeding with installation..."
+        check_os_version_pam_install
+        return
+        ;;
+      [Nn]* )
+        echo "Exiting to main menu. Please check your internet connection."
+        main_menu
+        return
+        ;;
+      * ) echo "Please answer Y (yes) or N (no).";;
+    esac
+  done
+}
+
+#=================== SYSTEM UTILITIES ===================
+restart_ssh_service() {
+  systemctl restart sshd 2>/dev/null && print_green "SSH restarted" && return
+  service ssh restart 2>/dev/null && print_green "SSH restarted" && return
+  service sshd restart 2>/dev/null && print_green "SSH restarted" && return
+  print_yellow "Could not restart SSH"
+}
+
+review_user_accounts() {
+  show_security_animation 1
+  echo "🔍 System user accounts:"
+  echo "------------------------"
+  awk -F: '$7 ~ /\/(bash|sh|zsh|fish)$/ {printf "👤 %-15s (UID: %s, Shell: %s)\n", $1, $3, $7}' /etc/passwd
+  echo ""
+  echo "🔐 Users with sudo access:"
+  echo "-------------------------"
+  if getent group sudo >/dev/null 2>&1; then
+    getent group sudo | cut -d: -f4 | tr ',' '\n' | while read user; do
+      [[ -n "$user" ]] && echo "🔑 $user"
+    done
+  fi
+}
+
+show_security_animation() {
+  local chars=('🔒' '🔓' '🔐' '🛡️')
+  local messages=('Initializing...' 'Checking integrity...' 'Validating security...' 'Ready!')
+  local delay=0.2
+  local duration=${1:-5}
+  local end_time=$((SECONDS + duration))
+  local msg_index=0
+  while [ $SECONDS -lt $end_time ]; do
+    for (( i = 0; i < ${#chars[@]}; i++ )); do
+      printf "\r\033[36m%s %s\033[0m%-20s" "${chars[$i]}" "${messages[$msg_index]}" " "
+      sleep $delay
+      if [ $SECONDS -ge $end_time ]; then break; fi
+    done
+    msg_index=$(((msg_index + 1) % ${#messages[@]}))
+  done
+  printf "\r\033[37m==== Security check complete! ====\033[0m\n"
+}
+
+create_sysadmin_user() {
+  echo -n "👤 Enter new username: "
+  read -r new_user
+  if id "$new_user" &>/dev/null; then
+    echo -e "⚠️  User \e[1;33m$new_user\e[0m already exists."
+    return
+  fi
+  if [ -f /etc/os-release ]; then
+    . /etc/os-release
+    os_name=$ID
+  else
+    echo -e "❌ Cannot detect OS."
+    return 1
+  fi
+  echo "🔧 Creating user: $new_user"
+  useradd -m "$new_user"
+  echo -e "📢 Set password for $new_user:"
+  passwd "$new_user"
+  if [[ "$os_name" == "almalinux" || "$os_name" == "centos" || "$os_name" == "rhel" ]]; then
+    usermod -aG wheel "$new_user"
+    echo -e "✅ Added \e[1;32m$new_user\e[0m to group \e[1;34mwheel\e[0m (sudo access)"
+  elif [[ "$os_name" == "ubuntu" || "$os_name" == "debian" ]]; then
+    usermod -aG sudo "$new_user"
+    echo -e "✅ Added \e[1;32m$new_user\e[0m to group \e[1;34msudo\e[0m (sudo access)"
+  else
+    echo -e "⚠️  Unknown distro. You may need to manually assign sudo group."
+  fi
+  SFTP_PATH="/usr/libexec/openssh/sftp-server"
+  SUDOERS_FILE="/etc/sudoers.d/$new_user"
+  echo "$new_user ALL=(ALL) NOPASSWD: $SFTP_PATH" > "$SUDOERS_FILE"
+  chmod 440 "$SUDOERS_FILE"
+  if grep -q "$SFTP_PATH" "$SUDOERS_FILE"; then
+    echo -e "✅ Added \e[1;32mNOPASSWD SFTP\e[0m for $new_user at $SUDOERS_FILE"
+  else
+    echo -e "⚠️  Failed to update $SUDOERS_FILE. Please check manually."
+  fi
+  echo ""
+  echo -e "📌 You can verify with: \e[1;33mcat $SUDOERS_FILE\e[0m"
+  echo -e "✏️  Or edit manually with: \e[1;33mvisudo -f $SUDOERS_FILE\e[0m"
+}
+
+check_and_fix_dns() {
+  echo -e "\n🌐 Checking DNS resolution..."
+  if ping -c 1 -W 2 google.com >/dev/null 2>&1; then
+    echo -e "DNS Resolve: \e[1;32m✅ Working\e[0m"
+  else
+    echo -e "DNS Resolve: \e[1;31m❌ Failed\e[0m"
+    echo -e "\n📄 Current DNS config in /etc/resolv.conf:"
+    grep "^nameserver" /etc/resolv.conf
+    echo -ne "\n🛠️  Would you like to replace DNS with Google DNS (8.8.8.8)? [y/N]: "
+    read -r choice
+    if [[ "$choice" =~ ^[Yy]$ ]]; then
+      cp /etc/resolv.conf /etc/resolv.conf.bak.$(date +%s)
+      sed -i 's/^nameserver/#nameserver/' /etc/resolv.conf
+      sed -i '1inameserver 8.8.8.8' /etc/resolv.conf
+      echo -e "\n✅ Updated /etc/resolv.conf to use Google DNS."
+      echo "🔁 Try ping google.com again to verify."
+    else
+      echo -e "🚫 DNS config not changed."
+    fi
+  fi
+}
+
+#=================== LOGOS AND MENUS ===================
+crowdstrike_logo() {
+  echo -e "\e[1;31m"
+  echo " ▗▄▄▖▗▄▄▖  ▗▄▖ ▗▖ ▗▖▗▄▄▄  ▗▄▄▖▗▄▄▄▖▗▄▄▖ ▗▄▄▄▖▗▖ ▗▖▗▄▄▄▖    ▗▄▄▄▖ ▗▄▖ ▗▖    ▗▄▄▖ ▗▄▖ ▗▖  ▗▖"
+  echo "▐▌   ▐▌ ▐▌▐▌ ▐▌▐▌ ▐▌▐▌  █▐▌     █  ▐▌ ▐▌  █  ▐▌▗▞▘▐▌       ▐▌   ▐▌ ▐▌▐▌   ▐▌   ▐▌ ▐▌▐▛▚▖▐▌"
+  echo "▐▌   ▐▛▀▚▖▐▌ ▐▌▐▌ ▐▌▐▌  █ ▝▀▚▖  █  ▐▛▀▚▖  █  ▐▛▚▖ ▐▛▀▀▘    ▐▛▀▀▘▐▛▀▜▌▐▌   ▐▌   ▐▌ ▐▌▐▌ ▝▜▌"
+  echo "▝▚▄▄▖▐▌ ▐▌▝▚▄▞▘▐▙█▟▌▐▙▄▄▀▗▄▄▞▘  █  ▐▌ ▐▌▗▄█▄▖▐▌ ▐▌▐▙▄▄▖    ▐▌   ▐▌ ▐▌▐▙▄▄▖▝▚▄▄▖▝▚▄▞▘▐▌  ▐▌"
+  echo -e "\e[0m"
+}
+
+sentinelone_logo() {
+  echo -e "\e[1;35m"
+  echo " ▗▄▄▖▗▄▄▄▖▗▖  ▗▖▗▄▄▄▖▗▄▄▄▖▗▖  ▗▖▗▄▄▄▖▗▖    ▗▄▖ ▗▖  ▗▖▗▄▄▄▖"
+  echo "▐▌   ▐▌   ▐▛▚▖▐▌  █    █  ▐▛▚▖▐▌▐▌   ▐▌   ▐▌ ▐▌▐▛▚▖▐▌▐▌   "
+  echo " ▝▀▚▖▐▛▀▀▘▐▌ ▝▜▌  █    █  ▐▌ ▝▜▌▐▛▀▀▘▐▌   ▐▌ ▐▌▐▌ ▝▜▌▐▛▀▀▘"
+  echo "▗▄▄▞▘▐▙▄▄▖▐▌  ▐▌  █  ▗▄█▄▖▐▌  ▐▌▐▙▄▄▖▐▙▄▄▖▝▚▄▞▘▐▌  ▐▌▐▙▄▄▖"
+  echo -e "\e[0m"
+}
+
+siem_logo() {
+  echo -e "\e[1;33m"
+  echo "                                               "
+  echo "                                        ____   "
+  echo "              ,--,                    ,'  , \`. "
+  echo "            ,--.'|                 ,-+-,.' _ | "
+  echo "  .--.--.   |  |,               ,-+-. ;   , || "
+  echo " /  /    '  \`--'_       ,---.  ,--.'|'   |  || "
+  echo "|  :  \`./  ,' ,'|     /     \|   |  ,', |  |, "
+  echo "|  :  ;_    '  | |    /    /  |   | /  | |--'  "
+  echo " \  \    \`. |  | :   .    ' / |   : |  | ,     "
+  echo "  \`----.   \\  : |__ '   ;   /|   : |  |/      "
+  echo " /  \`--'  /|  | '.'|'   |  / |   | |\`-'        "
+  echo "'--'.     / ;  :    ;|   :    |   ;/            "
+  echo "  \`--'---'  |  ,   /  \   \  /'---'             "
+  echo "             ---\`-'    \`----'                  "
+  echo -e "\e[0m"
+}
+
+crowdstrike_menu() {
+  clear
+  crowdstrike_logo
+  echo -e "\n\e[1;31mCrowdstrike Falcon Menu\e[0m"
+  echo "1) Install Crowdstrike"
+  echo "2) Uninstall Crowdstrike"
+  read -p "Select: " cs
+  case "$cs" in
+    1) echo "Installing Crowdstrike..." ;;
+    2) echo "Uninstalling Crowdstrike..." ;;
+    *) echo "Invalid option." ;;
+  esac
+  read -p "Press Enter to return to Main Menu..."
+}
+
+sentinelone_menu() {
+  clear
+  sentinelone_logo
+  echo -e "\n\e[1;35mSentinelOne Menu\e[0m"
+  echo "1) Install SentinelOne"
+  echo "2) Uninstall SentinelOne"
+  read -p "Select: " s1
+  case "$s1" in
+    1) echo "Installing SentinelOne..." ;;
+    2) echo "Uninstalling SentinelOne..." ;;
+    *) echo "Invalid option." ;;
+  esac
+  read -p "Press Enter to return to Main Menu..."
+}
+
+duo_menu() {
+  while true; do
+    clear
+    duo_logo
+    echo -e "\n\e[1;32m==== DUO SECURITY & TROUBLESHOOT MENU ====\e[0m"
+    echo "1) Install Duo"
+    echo "2) Uninstall Duo"
+    echo "3) Check Tools"
+    echo "4) Restart SSH"
+    echo "5) Create User"
+    echo "6) Edit DNS"
+    echo "7) Edit Repo"
+    echo "0) 📍 Back to Main Menu"
+    echo -n "Enter choice: "
+    read -r d
+    case "$d" in
+      1) check_internet_install_duo ;;
+      2) uninstall_duo ;;
+      3) check_tools_and_install ;;
+      4) restart_ssh_service ;;
+      5) create_sysadmin_user ;;
+      6) check_and_fix_dns ;;
+      7) settings ;;
+      0) break ;;
+      *) echo -e "\e[1;31m❌ Invalid choice.\e[0m" ;;
+    esac
+    echo
+    read -p "Press Enter to return to Duo Menu..."
+  done
+}
+
+siem_menu() {
+  clear
+  siem_logo
+  echo -e "\nSIEM Menu"
+  echo "1) Install rsyslog"
+  echo "2) Test Sendloging"
+  echo "3) Uninstall rsyslog"
+  echo "4) Install Agent"
+  echo "5) Uninstall Agent"
+  read -p "Select: " s
+  case "$s" in
+    1) setup_rsyslog_forwarding ;;
+    2) logger "Test log from SIEM menu" ;;
+    3) echo "Uninstalling rsyslog..." && yum remove -y rsyslog || apt remove -y rsyslog ;;
+    4) echo "Installing SIEM Agent..." ;;
+    5) echo "Uninstalling SIEM Agent..." ;;
+    *) echo "Invalid option." ;;
+  esac
+  read -p "Press Enter to return to Main Menu..."
+}
+
+show_main_logo() {
+  echo -e "\e[1;32m"
+  echo ".####.##....##..######..########....########..#######...#######..##........######..########..######."
+  echo "..##..###...##.##....##....##..........##....##.....##.##.....##.##.......##....##.##.......##....##"
+  echo "..##..####..##.##..........##..........##....##.....##.##.....##.##.......##.......##.......##......"
+  echo "..##..##.##.##..######.....##..........##....##.....##.##.....##.##........######..######...##......"
+  echo "..##..##..####.......##....##..........##....##.....##.##.....##.##.............##.##.......##......"
+  echo "..##..##...###.##....##....##..........##....##.....##.##.....##.##.......##....##.##.......##....##"
+  echo ".####.##....##..######.....##..........##.....#######...#######..########..######..########..######."
+  echo -e "\e[0m"
+  echo -e "\e[1;34m--------------------------[\e[1;37m Version $SCRIPT_VERSION \e[1;34m]--------------------------\e[0m"
+  check_connectivity_status
+}
+
+main_menu() {
+  while true; do
+    clear
+    show_main_logo
+    echo -e "\e[1;37;42m<==== SECURITY TOOLKIT MENU ====>\e[0m"
+    echo -e "1) \e[1;31mCrowdstrike Falcon\e[0m"
+    echo -e "2) \e[1;35mSentinelOne\e[0m"
+    echo -e "3) \e[1;32mDuo Security & Troubleshoot\e[0m"
+    echo -e "4) \e[1;37mSIEM\e[0m"
+    echo -e "9) Exit"
+    echo -n "Enter your choice: "
+    read -r choice
+    case "$choice" in
+      1) crowdstrike_menu ;;
+      2) sentinelone_menu ;;
+      3) duo_menu ;;
+      4) siem_menu ;;
+      9) echo "👋 Exiting... โชคดี ขอให้ทุกอย่างเรียบร้อย" && break ;;
+      *) echo "❌ Invalid option. หากต้องการออกกด 9" && sleep 1 ;;
+    esac
+  done
+}
+
+#=================== SETTINGS & VERSION ===================
+SELECTED_VERSION="duo_unix-2.0.3.tar.gz"
+
+fetch_release_notes() {
+  local VERSION_TAG=$1
+  local USER="duosecurity"
+  local REPO="duo_unix"
+  local API_URL="https://api.github.com/repos/$USER/$REPO/releases/tags/$VERSION_TAG"
+  echo "Fetching release notes for $VERSION_TAG..."
+  HTTP_RESPONSE=$(curl -s -w "%{http_code}" -o response.json "$API_URL")
+  if [ "$HTTP_RESPONSE" -ne 200 ]; then
+    echo "Error: Failed to fetch release notes (HTTP Status: $HTTP_RESPONSE)."
+    rm -f response.json
+    return
+  fi
+  RELEASE_NOTES=$(grep -oP '"body":\s*"\K[^"]+' response.json)
+  if [ -z "$RELEASE_NOTES" ]; then
+    echo "No release notes found for $VERSION_TAG."
+  else
+    print_green "Release Notes for $VERSION_TAG:"
+    echo "--------------------------------------------"
+    echo ""
+    print_green "$RELEASE_NOTES"
+    echo ""
+    echo "--------------------------------------------"
+  fi
+  rm -f response.json
+}
+
+settings() {
+  echo "Settings Menu - Choose a Duo Unix version to download:"
+  echo "1) Duo unix latest"
+  echo "2) Duo unix .0.42"
+  echo "3) Duo unix 2.0.3 (Default)"
+  echo "4) Duo unix 2.0.2"
+  echo "5) Duo unix 2.0.1"
+  echo "6) Duo unix 2.0.0"
+  echo "0) Return to main menu"
+  read -p "Choose a version (1-6): " CHOICE
+  case $CHOICE in
+    1) SELECTED_VERSION="duo_unix-latest.tar.gz";;
+    2) SELECTED_VERSION="duo_unix-2.0.4.tar.gz"; fetch_release_notes "duo_unix-2.0.4";;
+    3) SELECTED_VERSION="duo_unix-2.0.3.tar.gz"; fetch_release_notes "duo_unix-2.0.3";;
+    4) SELECTED_VERSION="duo_unix-2.0.2.tar.gz"; fetch_release_notes "duo_unix-2.0.2";;
+    5) SELECTED_VERSION="duo_unix-2.0.1.tar.gz"; fetch_release_notes "duo_unix-2.0.1";;
+    6) SELECTED_VERSION="duo_unix-2.0.0.tar.gz"; fetch_release_notes "duo_unix-2.0.0";;
+    0) main_menu; return;;
+    *) echo "Invalid choice. Returning to settings..."; read -p "Press Enter to return to the menu..."; settings;;
+  esac
+  read -p "Save this version as default (Y/n)? " CONFIRMATION
+  if [[ "$CONFIRMATION" =~ ^[Yy]$ || -z "$CONFIRMATION" ]]; then
+    print_green "Version $SELECTED_VERSION saved as default."
+  else
+    print_red "Version not saved. Returning to settings..."
+    read -p "Press Enter to return to the menu..."
+    main_menu
+  fi
+}
+
+#=================== PERMISSION & TELEGRAM ===================
+check_root_permission() {
+  if [ "$EUID" -ne 0 ]; then
+    print_red ""-------------------------------""
+    print_red "This script must be run as root."
+    print_red ""-------------------------------""
+    echo ""
+    exit 1
+  fi
+}
+
+ask_installer_info_once() {
+  if [ -z "$INSTALLER_NAME" ] || [ -z "$HOSPITAL_CODE" ]; then
+    echo ""
+    echo "📋 Please provide installation information"
+    echo ""
+    read -p "👤 Installer Name: " input_name
+    while [[ -z "$input_name" ]]; do
+      echo -e "\033[31mInstaller Name cannot be empty.\033[0m"
+      read -p "👤 Installer Name: " input_name
+    done
+    read -p "🏥 Hospital Code: " input_code
+    while [[ -z "$input_code" ]]; do
+      echo -e "\033[31mHospital Code cannot be empty.\033[0m"
+      read -p "🏥 Hospital Code: " input_code
+    done
+    export INSTALLER_NAME="$input_name"
+    export HOSPITAL_CODE="$input_code"
+    echo -e "\n\033[32m✔️ Captured:\033[0m \033[1;36m$INSTALLER_NAME @ Hospital ($HOSPITAL_CODE)\033[0m"
+    echo ""
+    sleep 1
+  fi
+}
+
+send_telegram_alert() {
+  IP_ADDRESS=$(hostname -I | awk '{print $1}')
+  HOSTNAME=$(hostname)
+  OS=$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
+  OS_VER=$(grep '^VERSION_ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
+  MAC_ADDR=$(ip link show | awk '/ether/ {print $2}' | head -n 1)
+MESSAGE=$(cat <<EOF_MSG
+📦 *DUO SECURITY REPORT*
+\`\`\`
+Name          : $INSTALLER_NAME
+Hospital Code : $HOSPITAL_CODE
+IP Address    : $IP_ADDRESS
+Hostname      : $HOSTNAME
+OS            : ${OS^} ${OS_VER}
+MAC Address   : $MAC_ADDR
+\`\`\`
+✅ Status: Completed!..
+EOF_MSG
+)
+  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
+    -d "chat_id=${TELEGRAM_CHAT_ID}" \
+    -d "parse_mode=Markdown" \
+    -d "text=${MESSAGE}" > /dev/null
+}
+
+#=================== STARTUP ===================
+check_root_permission
+auto_update
+ask_installer_info_once
+ensure_clear_installed
+main_menu
 
EOF
)
