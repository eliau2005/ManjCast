#!/bin/bash
# ManjCast - Screen Casting Tool for Manjaro Linux
# Installation Script

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${NC}"
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_message "$RED" "Please do not run as root. The script will use sudo when needed."
        exit 1
    fi
}

# Check system dependencies
check_dependencies() {
    print_message "$BLUE" "Checking system dependencies..."
    
    local missing_deps=()
    
    # Check for Python 3.8+
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    else
        python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ $(echo "$python_version < 3.8" | bc) -eq 1 ]]; then
            print_message "$YELLOW" "Python version $python_version is too old. ManjCast requires Python 3.8+."
            missing_deps+=("python3>=3.8")
        fi
    fi
    
    # Check for ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        missing_deps+=("ffmpeg")
    fi
    
    # Check for PulseAudio
    if ! command -v pactl &> /dev/null; then
        missing_deps+=("pulseaudio")
    fi
    
    # Check for X11 utilities
    if ! command -v xwininfo &> /dev/null; then
        missing_deps+=("xorg-xwininfo")
    fi
    
    if ! command -v xdotool &> /dev/null; then
        missing_deps+=("xdotool")
    fi
    
    # If there are missing dependencies, ask to install them
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_message "$YELLOW" "The following dependencies are missing:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        
        read -p "Do you want to install them now? (y/N) " install_choice
        if [[ "$install_choice" == "y" || "$install_choice" == "Y" ]]; then
            print_message "$BLUE" "Installing missing dependencies..."
            sudo pacman -S --needed "${missing_deps[@]}"
            
            # Check if installation was successful
            for dep in "${missing_deps[@]}"; do
                # Extract package name (before any version specifier)
                pkg_name=$(echo "$dep" | cut -d '>' -f 1 | cut -d '=' -f 1)
                if ! pacman -Q "$pkg_name" &> /dev/null; then
                    print_message "$RED" "Failed to install $pkg_name. Please install it manually and try again."
                    exit 1
                fi
            done
        else
            print_message "$RED" "Dependencies must be installed to continue. Please install them manually and try again."
            exit 1
        fi
    fi
    
    print_message "$GREEN" "All system dependencies are met."
}

# Install Python dependencies
install_python_deps() {
    print_message "$BLUE" "Installing Python dependencies..."
    
    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        print_message "$YELLOW" "pip3 is not installed. Installing..."
        sudo pacman -S --needed python-pip
    fi
    
    # Create virtual environment (optional)
    read -p "Do you want to install ManjCast in a virtual environment? (y/N) " venv_choice
    if [[ "$venv_choice" == "y" || "$venv_choice" == "Y" ]]; then
        # Check if venv module is available
        if ! python3 -c "import venv" &> /dev/null; then
            print_message "$YELLOW" "Python venv module is not available. Installing..."
            sudo pacman -S --needed python-virtualenv
        fi
        
        # Create virtual environment
        print_message "$BLUE" "Creating virtual environment..."
        python3 -m venv "$HOME/.local/share/manjcast/venv"
        
        # Activate virtual environment for pip install
        source "$HOME/.local/share/manjcast/venv/bin/activate"
        
        # Install dependencies in virtual environment
        pip3 install -r "$(dirname "$0")/requirements.txt"
        
        # Create wrapper script
        mkdir -p "$HOME/.local/bin"
        cat > "$HOME/.local/bin/manjcast" << EOF
#!/bin/bash
# Wrapper script for ManjCast

# Activate virtual environment
source "$HOME/.local/share/manjcast/venv/bin/activate"

# Run ManjCast
python3 "$HOME/.local/share/manjcast/src/manjcast.py" "\$@"
EOF
        chmod +x "$HOME/.local/bin/manjcast"
        
        # Deactivate virtual environment
        deactivate
    else
        # Install dependencies system-wide for the current user
        pip3 install --user -r "$(dirname "$0")/requirements.txt"
        
        # Create launcher script
        mkdir -p "$HOME/.local/bin"
        cat > "$HOME/.local/bin/manjcast" << EOF
#!/bin/bash
# Launcher script for ManjCast

# Run ManjCast
python3 "$HOME/.local/share/manjcast/src/manjcast.py" "\$@"
EOF
        chmod +x "$HOME/.local/bin/manjcast"
    fi
    
    print_message "$GREEN" "Python dependencies installed."
}

# Copy application files
copy_app_files() {
    print_message "$BLUE" "Installing ManjCast files..."
    
    # Create application directories
    mkdir -p "$HOME/.local/share/manjcast/"{src,ui,assets,scripts}
    mkdir -p "$HOME/.config/manjcast"
    mkdir -p "$HOME/.local/share/manjcast/logs"
    
    # Copy source files
    cp -r "$(dirname "$0")/src/"* "$HOME/.local/share/manjcast/src/"
    cp -r "$(dirname "$0")/ui/"* "$HOME/.local/share/manjcast/ui/"
    cp -r "$(dirname "$0")/assets/"* "$HOME/.local/share/manjcast/assets/" 2>/dev/null || true
    cp -r "$(dirname "$0")/scripts/"* "$HOME/.local/share/manjcast/scripts/"
    
    # Copy config file (if it doesn't exist)
    if [ ! -f "$HOME/.config/manjcast/config.ini" ]; then
        cp "$(dirname "$0")/config.ini" "$HOME/.config/manjcast/"
    fi
    
    print_message "$GREEN" "ManjCast files installed."
}

# Setup desktop integration
setup_desktop_integration() {
    print_message "$BLUE" "Setting up desktop integration..."
    
    # Run desktop integration script
    bash "$HOME/.local/share/manjcast/scripts/desktop_integration.sh"
    
    print_message "$GREEN" "Desktop integration completed."
}

# Add .local/bin to PATH if not already there
add_to_path() {
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        print_message "$YELLOW" "Adding $HOME/.local/bin to PATH..."
        
        # Determine which shell config file to use
        shell_config=""
        if [ -n "$BASH_VERSION" ]; then
            if [ -f "$HOME/.bashrc" ]; then
                shell_config="$HOME/.bashrc"
            elif [ -f "$HOME/.bash_profile" ]; then
                shell_config="$HOME/.bash_profile"
            fi
        elif [ -n "$ZSH_VERSION" ]; then
            shell_config="$HOME/.zshrc"
        fi
        
        if [ -n "$shell_config" ]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$shell_config"
            print_message "$GREEN" "Added $HOME/.local/bin to PATH in $shell_config"
            print_message "$YELLOW" "Please restart your terminal or run 'source $shell_config' to update your PATH."
        else
            print_message "$YELLOW" "Could not determine shell config file. Please add $HOME/.local/bin to your PATH manually."
        fi
    fi
}

# Main installation function
main() {
    print_message "$BLUE" "=== ManjCast Installation ==="
    
    # Check if running as root
    check_root
    
    # Check system dependencies
    check_dependencies
    
    # Install Python dependencies
    install_python_deps
    
    # Copy application files
    copy_app_files
    
    # Setup desktop integration
    setup_desktop_integration
    
    # Add to PATH if needed
    add_to_path
    
    print_message "$GREEN" "=== ManjCast installation completed! ==="
    print_message "$GREEN" "You can run ManjCast by typing 'manjcast' in your terminal or launching it from your application menu."
}

# Run main function
main
