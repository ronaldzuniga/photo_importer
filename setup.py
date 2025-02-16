from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="photo-importer",
    version="0.1.0",
    author="Ronald Zúñiga",
    author_email="ronald@ronaldzuniga.com",
    description="A tool for organizing photos by date taken using EXIF metadata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ronaldzuniga/photo-importer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Topic :: Multimedia :: Graphics",
        "Topic :: System :: Filesystems",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "photo-importer=photo_importer.cli:main",
        ],
    },
)
