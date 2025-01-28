from setuptools import setup, find_packages

setup(
    name="osu-about-me-graph",
    version="1.0",
    packages=find_packages(),
    scripts=["bin/osu_mentions"],
    install_requires=[
        "ossapi~=3.0",
        "networkx~=3.0",
        "matplotlib~=3.0",
        "asyncio~=3.0",
        "aiohttp~=3.0",
        "python-dotenv~=1.0",
        "scipy~=1.0",
        "numpy~=2.0",
        "pillow~=11.0"
    ]
)
