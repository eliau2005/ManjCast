#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="manjcast",
    version="1.0.0",
    author="ManjCast Contributors",
    author_email="your.email@example.com",
    description="Screen Casting Tool for Manjaro Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/manjcast",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.8',
    install_requires=[
        "PyQt5>=5.15.0",
        "pychromecast>=10.2.3",
        "zeroconf>=0.38.6",
        "python-xlib>=0.31",
        "pulsectl>=22.3.2",
        "ffmpeg-python>=0.2.0",
        "dbus-python>=1.2.18",
        "psutil>=5.9.0",
        "requests>=2.27.1",
        "pillow>=9.0.0",
        "numpy>=1.22.0"
    ],
    entry_points={
        'console_scripts': [
            'manjcast=src.manjcast:main',
        ],
    },
    include_package_data=True,
    data_files=[
        ('share/applications', ['ManjCast.desktop']),
        ('share/manjcast', ['config.ini']),
        ('share/icons/hicolor/128x128/apps', ['assets/manjcast.png']),
    ],
) 