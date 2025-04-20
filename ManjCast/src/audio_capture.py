#!/usr/bin/env python3
# ManjCast - Screen Casting Tool for Manjaro Linux
# Audio Capture Module

import logging
import subprocess
import os
import time
import threading
import re
from typing import Optional, List, Dict, Any, Union

# pulsectl is a PulseAudio control library
# It is listed in requirements.txt/setup.py, but we handle the case
# where it's not installed with a fallback mechanism
try:
    import pulsectl
    # Define type alias for IDE recognition
    Pulse = pulsectl.Pulse
    PULSECTL_AVAILABLE = True
except ImportError:
    # Create a dummy type for type checking
    class Pulse:  # type: ignore
        """Dummy class when pulsectl is not available"""
        pass
    PULSECTL_AVAILABLE = False

logger = logging.getLogger("ManjCast.AudioCapture")

class AudioCapture:
    """Handles capturing system audio for casting"""
    
    def __init__(self, config):
        self.config = config
        self.is_capturing = False
        self.audio_source = "default"
        self.pulse: Optional[Pulse] = None
        
        # Initialize PulseAudio connection if available
        if PULSECTL_AVAILABLE:
            try:
                self.pulse = pulsectl.Pulse('manjcast-audio')
                logger.info("PulseAudio connection established")
            except Exception as e:
                logger.error(f"Error connecting to PulseAudio: {e}")
    
    def get_audio_sources(self) -> List[Dict[str, Any]]:
        """Get a list of available audio sources"""
        sources = []
        
        if self.pulse:
            try:
                # Get all sinks (audio outputs)
                sinks = self.pulse.sink_list()
                for sink in sinks:
                    sources.append({
                        'id': sink.name,
                        'name': sink.description,
                        'type': 'sink'
                    })
                
                # Get all source outputs (applications producing audio)
                source_outputs = self.pulse.source_output_list()
                for source in source_outputs:
                    # Skip any system-related sources
                    if "System Sounds" in source.name or "manjcast" in source.name.lower():
                        continue
                    
                    sources.append({
                        'id': source.index,
                        'name': source.name,
                        'type': 'source'
                    })
                
                logger.info(f"Found {len(sources)} audio sources")
                return sources
            except Exception as e:
                logger.error(f"Error listing audio sources: {e}")
        
        # Fallback - try to use system commands if PulseAudio API failed
        try:
            # Try using pactl to list sinks
            output = subprocess.check_output(["pactl", "list", "short", "sinks"]).decode()
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        sink_id = parts[0]
                        sink_name = parts[1]
                        sources.append({
                            'id': sink_name,
                            'name': f"Audio Output {sink_id}",
                            'type': 'sink'
                        })
        except Exception as e:
            logger.error(f"Error listing audio sinks with pactl: {e}")
            
            # Add a default audio source
            sources.append({
                'id': 'default',
                'name': 'System Default',
                'type': 'default'
            })
        
        return sources
    
    def set_audio_source(self, source_id: str):
        """Set the audio source to capture"""
        self.audio_source = source_id
        logger.info(f"Audio source set to {source_id}")
    
    def get_source(self) -> str:
        """Get the audio source identifier for ffmpeg"""
        return self.audio_source
    
    def start_capture(self) -> bool:
        """Start audio capture"""
        if self.is_capturing:
            logger.warning("Audio capture is already running")
            return False
        
        try:
            # For PulseAudio, we don't need to start anything explicitly here
            # The actual capture will be performed by ffmpeg in the cast_manager
            
            # Set up a monitor source if needed
            if self.pulse and self.audio_source != "default":
                try:
                    # If the source is a sink, create a monitor source for it
                    sink = self.pulse.get_sink_by_name(self.audio_source)
                    if sink:
                        # Set the audio source to the monitor of this sink
                        self.audio_source = sink.name + ".monitor"
                        logger.info(f"Using monitor source: {self.audio_source}")
                except Exception as e:
                    logger.warning(f"Error setting up monitor source: {e}")
                    # Fall back to default
                    self.audio_source = "default"
            
            self.is_capturing = True
            logger.info("Audio capture started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting audio capture: {e}")
            return False
    
    def stop_capture(self):
        """Stop audio capture"""
        if not self.is_capturing:
            return
        
        try:
            # Nothing to stop - ffmpeg handles the actual capture
            self.is_capturing = False
            logger.info("Audio capture stopped")
            
        except Exception as e:
            logger.error(f"Error stopping audio capture: {e}")
    
    def get_volume(self) -> float:
        """Get the current system volume (0.0-1.0)"""
        if self.pulse:
            try:
                sinks = self.pulse.sink_list()
                if sinks:
                    # Use the first sink's volume
                    sink = sinks[0]
                    # Get the average of all channels
                    volume = self.pulse.volume_get_all_chans(sink)
                    return volume
            except Exception as e:
                logger.error(f"Error getting volume: {e}")
        
        # Fallback - try with amixer
        try:
            output = subprocess.check_output(["amixer", "sget", "Master"]).decode()
            match = re.search(r'(\d+)%', output)
            if match:
                volume_percent = int(match.group(1))
                return volume_percent / 100.0
        except Exception as e:
            logger.error(f"Error getting volume with amixer: {e}")
        
        # Return a default value
        return 1.0
    
    def set_volume(self, volume: float) -> bool:
        """Set the system volume (0.0-1.0)"""
        if not 0.0 <= volume <= 1.0:
            logger.error(f"Invalid volume level: {volume}")
            return False
        
        if self.pulse:
            try:
                sinks = self.pulse.sink_list()
                if sinks:
                    for sink in sinks:
                        self.pulse.volume_set_all_chans(sink, volume)
                    logger.info(f"Volume set to {volume:.2f}")
                    return True
            except Exception as e:
                logger.error(f"Error setting volume: {e}")
        
        # Fallback - try with amixer
        try:
            volume_percent = int(volume * 100)
            subprocess.run(["amixer", "sset", "Master", f"{volume_percent}%"])
            logger.info(f"Volume set to {volume_percent}%")
            return True
        except Exception as e:
            logger.error(f"Error setting volume with amixer: {e}")
        
        return False
    
    def mute(self, muted: bool = True) -> bool:
        """Mute or unmute the audio"""
        if self.pulse:
            try:
                sinks = self.pulse.sink_list()
                for sink in sinks:
                    self.pulse.mute(sink, muted)
                logger.info(f"Audio {'muted' if muted else 'unmuted'}")
                return True
            except Exception as e:
                logger.error(f"Error {'muting' if muted else 'unmuting'} audio: {e}")
        
        # Fallback - try with amixer
        try:
            subprocess.run(["amixer", "sset", "Master", "mute" if muted else "unmute"])
            logger.info(f"Audio {'muted' if muted else 'unmuted'}")
            return True
        except Exception as e:
            logger.error(f"Error {'muting' if muted else 'unmuting'} with amixer: {e}")
        
        return False
    
    def is_muted(self) -> bool:
        """Check if audio is muted"""
        if self.pulse:
            try:
                sinks = self.pulse.sink_list()
                if sinks:
                    return bool(sinks[0].mute)
            except Exception as e:
                logger.error(f"Error checking mute status: {e}")
        
        # Fallback - try with amixer
        try:
            output = subprocess.check_output(["amixer", "sget", "Master"]).decode()
            return "[off]" in output
        except Exception as e:
            logger.error(f"Error checking mute status with amixer: {e}")
        
        return False
    
    def __del__(self):
        """Clean up resources"""
        if self.pulse:
            try:
                self.pulse.close()
            except:
                pass
