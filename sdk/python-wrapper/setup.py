"""
Production-ready Semantis Cache SDK
Easy-to-use wrapper for semantic caching
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="semantis-cache",
    version="1.0.0",
    description="Semantis Cache - Semantic Caching SDK for LLM Applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Semantis AI",
    author_email="support@semantis.ai",
    url="https://github.com/semantis-ai/semantis-cache-python",
    packages=find_packages(include=["semantis_cache", "semantis_cache.*", "semantis_ai", "semantis_ai.*"]),
    install_requires=[
        "httpx>=0.23.0,<0.29.0",
        "attrs>=22.2.0",
        "python-dateutil>=2.8.0",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    keywords="semantic caching, llm, openai, cache, ai, semantic search",
    project_urls={
        "Documentation": "https://docs.semantis.ai",
        "Source": "https://github.com/semantis-ai/semantis-cache-python",
        "Issues": "https://github.com/semantis-ai/semantis-cache-python/issues",
    },
    include_package_data=True,
)
