from setuptools import setup, find_packages

setup(
    name="superinstance-luciddreamer",
    version="0.1.0",
    description="The meta-package: multi-agent dream radio station that auto-assembles all modules",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Lucineer / Casey DiGenaro",
    author_email="casey@superinstance.com",
    url="https://github.com/superinstance/luciddreamer",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "superinstance-conductor>=0.1.0",
        "superinstance-streamer>=0.1.0",
        "superinstance-knowledge-base>=0.1.0",
        "superinstance-sonic-shape>=0.1.0",
    ],
    extras_require={
        "config": ["pyyaml>=6.0"],
        "dev": ["pytest>=7.0", "pyyaml>=6.0"],
    },
    entry_points={
        "console_scripts": [
            "luciddreamer = luciddreamer.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Multimedia :: Sound/Audio",
    ],
)
