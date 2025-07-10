"""
Video Caption Generator - Setup Configuration
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="video-caption-generator",
    version="1.0.0",
    author="Video Caption Generator Team",
    author_email="contact@videocaption.dev",
    description="A CLI tool to extract speech from videos and translate to target languages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/video_caption_generator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "video-caption=caption_generator:main",
            "vcg=caption_generator:main",  # Short alias
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", ".env.example"],
    },
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.8.0",
            "pre-commit>=3.5.0",
        ],
        "gpu": [
            "torch>=2.3.1+cu121",  # GPU version
            "torchaudio>=2.3.1+cu121",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/video_caption_generator/issues",
        "Source": "https://github.com/yourusername/video_caption_generator",
        "Documentation": "https://github.com/yourusername/video_caption_generator/wiki",
    },
)