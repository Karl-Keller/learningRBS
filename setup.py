from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rete-engine",
    version="0.1.0",
    author="Your Name",
    author_email="sttorry@hotmail.com",
    description="Pattern-matched inference engine with Rete algorithm",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Karl-Keller/learningRBS",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.20.0",
    ],
    extras_require={
        "viz": [
            "matplotlib>=3.4.0",
            "networkx>=2.6.0",
            "pillow>=8.0.0",
        ],
        "dev": [
            "pytest>=6.0.0",
            "sphinx>=4.0.0",
        ],
    },
)