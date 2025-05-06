"""
Setup script for ManjCast application.
"""

from setuptools import setup, find_packages

setup(
    name="manjcast",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PySide6>=6.9.0",
        "pychromecast>=14.0.0",
        "zeroconf>=0.147.0",
        "ffmpeg-python>=0.2.0",
        "qt-material>=2.14",
    ],
    entry_points={
        'gui_scripts': [
            'manjcast=manjcast.main:main',
        ],
    },
    author="ManjCast Developer",
    description="Screen casting application for Manjaro Linux",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="chromecast, screen casting, manjaro",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Video",
    ],
    python_requires=">=3.9",
    include_package_data=True,
    package_data={
        'manjcast': ['resources/*'],
    },
)