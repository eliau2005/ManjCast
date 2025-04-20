#!/bin/bash
# ManjCast - Screen Casting Tool for Manjaro Linux
# Desktop Integration Script

# Detect desktop environment
detect_desktop_env() {
    if [ -n "$XDG_CURRENT_DESKTOP" ]; then
        desktop_env=$(echo "$XDG_CURRENT_DESKTOP" | tr '[:upper:]' '[:lower:]')
    elif [ -n "$DESKTOP_SESSION" ]; then
        desktop_env=$(echo "$DESKTOP_SESSION" | tr '[:upper:]' '[:lower:]')
    else
        # Try to detect based on running processes
        if pgrep -x "plasmashell" > /dev/null; then
            desktop_env="kde"
        elif pgrep -x "gnome-shell" > /dev/null; then
            desktop_env="gnome"
        elif pgrep -x "xfwm4" > /dev/null; then
            desktop_env="xfce"
        else
            desktop_env="unknown"
        fi
    fi
    
    echo "$desktop_env"
}

# Create desktop entry
create_desktop_entry() {
    local desktop_env="$1"
    local entry_dir="$HOME/.local/share/applications"
    local install_dir="$HOME/.local/bin"
    
    # Create directories if they don't exist
    mkdir -p "$entry_dir"
    
    # Write desktop entry file
    cat > "$entry_dir/manjcast.desktop" << EOF
[Desktop Entry]
Type=Application
Name=ManjCast
Comment=Screen Casting for Manjaro
GenericName=Screen Casting Tool
Exec=${install_dir}/manjcast
Icon=video-display
Terminal=false
Categories=Utility;AudioVideo;
Keywords=screencast;cast;stream;chromecast;tv;
EOF
    
    # Add desktop environment specific entries
    if [[ "$desktop_env" == *"kde"* ]]; then
        cat >> "$entry_dir/manjcast.desktop" << EOF
X-KDE-StartupNotify=true
X-DBUS-ServiceName=org.manjcast
EOF
    elif [[ "$desktop_env" == *"gnome"* ]]; then
        cat >> "$entry_dir/manjcast.desktop" << EOF
X-GNOME-UsesNotifications=true
EOF
    elif [[ "$desktop_env" == *"xfce"* ]]; then
        cat >> "$entry_dir/manjcast.desktop" << EOF
X-XFCE-Source=file://${install_dir}/manjcast
EOF
    fi
    
    # Make desktop entry executable
    chmod +x "$entry_dir/manjcast.desktop"
    
    echo "Desktop entry created at $entry_dir/manjcast.desktop"
}

# Create autostart entry
create_autostart_entry() {
    local desktop_env="$1"
    local autostart_dir="$HOME/.config/autostart"
    local install_dir="$HOME/.local/bin"
    
    # Create directory if it doesn't exist
    mkdir -p "$autostart_dir"
    
    # Copy desktop entry (with modifications if needed)
    if [ -f "$HOME/.local/share/applications/manjcast.desktop" ]; then
        cp "$HOME/.local/share/applications/manjcast.desktop" "$autostart_dir/"
        
        # Add autostart specific entries
        if [[ "$desktop_env" == *"kde"* ]]; then
            sed -i 's/\[Desktop Entry\]/[Desktop Entry]\nX-KDE-autostart-after=panel\nX-KDE-autostart-phase=2/' "$autostart_dir/manjcast.desktop"
        elif [[ "$desktop_env" == *"gnome"* ]]; then
            sed -i 's/\[Desktop Entry\]/[Desktop Entry]\nX-GNOME-Autostart-enabled=true/' "$autostart_dir/manjcast.desktop"
        fi
        
        echo "Autostart entry created at $autostart_dir/manjcast.desktop"
    else
        echo "ERROR: Desktop entry not found, cannot create autostart entry"
        return 1
    fi
}

# Create application directories
create_app_directories() {
    # Create config directory
    mkdir -p "$HOME/.config/manjcast"
    
    # Create data directory
    mkdir -p "$HOME/.local/share/manjcast/logs"
    
    echo "Application directories created"
}

# Main script logic
main() {
    # Get desktop environment
    desktop_env=$(detect_desktop_env)
    echo "Detected desktop environment: $desktop_env"
    
    # Create application directories
    create_app_directories
    
    # Create desktop entry
    create_desktop_entry "$desktop_env"
    
    # Ask about autostart
    read -p "Do you want ManjCast to start automatically with your desktop? (y/N) " autostart_choice
    if [[ "$autostart_choice" == "y" || "$autostart_choice" == "Y" ]]; then
        create_autostart_entry "$desktop_env"
    fi
    
    echo "Desktop integration completed."
}

# Execute main function
main
