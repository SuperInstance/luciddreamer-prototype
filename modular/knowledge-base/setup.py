from setuptools import setup, find_packages

setup(
    name="superinstance-knowledge-base",
    version="0.1.0",
    description="Recursive idea graph with contradiction detection, convergence clustering, and lineage tracking",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Lucineer / Casey DiGenaro",
    author_email="casey@superinstance.com",
    url="https://github.com/superinstance/knowledge-base",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[],  # pure Python
    extras_require={
        "embeddings": [],  # requires ollama running locally
        "cloudflare": [],  # requires wrangler CLI
        "dev": ["pytest>=7.0"],
    },
    entry_points={
        "console_scripts": [
            "luciddreamer-kb = knowledge_base.query:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
