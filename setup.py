from pathlib import Path

from setuptools import setup

about = {}
with open(Path("mapID_to_collection_DB/__version__.py").resolve(), "r",  encoding="utf-8") as v:
    exec(v.read(), about)


def get_long_description() -> str:
    try:
        fname = Path(__file__).resolve().joinpath("README.md")

    except (OSError, RuntimeError):
        raise NotImplementedError("README.md not found")

    with open(fname, "r") as f:
        return f.read()




setup(
    name=about["__title__"],
    description=about["__description__"],
    long_description=get_long_description(),
    author=about["__author__"],
    author_email=about["__author_email__"],
    license=about["__license__"],
    url=about["__url__"],
    download_url="",
    install_requires=[
        "requests"
    ],
    python_requires=">=3.10",
    project_urls={
        "Issue Tracker": "https://github.com/Kuuuube/osu_MapID_to_Collection_DB/issues",
        "Source": "https://github.com/Kuuuube/osu_MapID_to_Collection_DB",
    },
    version=about["__version__"],
)