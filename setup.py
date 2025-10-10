from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="contractguard-ai",
    version="1.0.0",
    author="Amen Ikamba",
    author_email="team@contractguard.ai",
    description="Autonomous AI agent for contract review and negotiation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amen-ikamba/contractguard-ai",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Legal Industry",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Framework :: FastAPI",
        "Framework :: AWS CDK",
    ],
    python_requires=">=3.11,<3.14",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "contractguard=src.web.app:main",
        ],
    },
)