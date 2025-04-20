# ManjCast - Screen Casting Tool for Manjaro

ManjCast is a user-friendly screen casting application designed specifically for Manjaro Linux that enables seamless screen casting to Android smart TVs. It works across KDE Plasma, GNOME, and XFCE desktop environments.

## Features

- **Screen Mirroring**: Cast your entire desktop or a specific application window
- **Audio Casting**: Stream system audio along with video
- **Device Discovery**: Automatically discover compatible Android TVs using Google Cast protocol
- **Simple UI**: Easy-to-use interface accessible from system tray
- **Cross-DE Support**: Works on KDE Plasma, GNOME, and XFCE
- **Low Latency**: Optimized for smooth streaming experience at 1080p/30fps

## Requirements

- Manjaro Linux
- Python 3.8+
- ffmpeg
- PulseAudio
- Network connection (preferably WiFi on same network as TV)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/manjcast.git
cd manjcast

# Run the installation script
./install.sh
```

## Usage

1. Launch ManjCast from your application menu or run `manjcast` in terminal
2. Select your casting device from the discovered devices list
3. Choose whether to cast the entire screen or a specific window
4. Toggle audio casting if needed
5. Click "Start Casting" to begin

## Configuration

Configuration options are available in `~/.config/manjcast/config.ini`

## Troubleshooting

If you encounter issues:
- Ensure your TV and computer are on the same network
- Verify Google Cast is enabled on your Android TV
- Check firewall settings to ensure required ports are open

## License

This project is licensed under the MIT License - see the LICENSE file for details.
