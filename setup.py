from setuptools import setup, find_packages

setup(
    name="detorrent",
    version="1.0.0",
    description="Advanced OS Switching Technology",
    author="Detorrent Team",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.5.0",
        "psutil>=5.9.0"
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "detorrent=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Operating System",
    ],
)
