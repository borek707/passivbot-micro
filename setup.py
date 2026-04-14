from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="passivbot-micro",
    version="0.1.0",
    author="PassivBot Contributors",
    description="Lightweight crypto trading bot for small capital ($100-200)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/borek707/passivbot-micro",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "ccxt>=4.0.0",
        "numpy>=1.21.0",
    ],
)