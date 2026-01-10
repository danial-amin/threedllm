"""Setup script for ThreeDLLM."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="threedllm",
    version="0.1.0",
    author="",
    description="A Vision Language Model system for generating 3D objects from prompts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/threedllm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
    ],
    python_requires=">=3.8",
    install_requires=[
        "torch>=1.13.0",
        "numpy>=1.20.0",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "python-multipart>=0.0.6",
        "pydantic>=2.0.0",
        # shap-e must be installed separately: pip install git+https://github.com/openai/shap-e.git
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "threedllm=threedllm.cli:main",
            "threedllm-server=threedllm.api.server:main",
        ],
    },
)
