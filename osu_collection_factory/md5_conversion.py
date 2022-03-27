import logging

from pathlib import Path
from typing import Sequence

import util

logger = logging.getLogger(__name__)


def convert_md5s_to_db(s: util.Settings, md5s: Sequence[str]):
    """Function to convert a sequence of md5s to the .db file format.

    Parameters
    ----------
    s : util.Settings
        Settings to use
    md5s : Sequence[str]
        Squence of map md5s
    """
    settings = s.get()

    name = settings["collection_name"]
    path = Path(f"{settings['collection_path']}/{name}/.db") 

    logger.info("[INFO] - Starting MD5 to DB conversion")

    with open(path, "wb") as f:
        f.write(b"\x00\x00\x00\x00")  # arbitrary osu! version
        f.write((1).to_bytes(4, "little"))  # number of collections
        f.write(b"\x0b")  # spacer
        f.write(len(name).to_bytes(1, "little"))
        f.write(name.encode())  # name of collection
        f.write(len(md5s).to_bytes(4, "little"))  # length of collection
        for md5 in md5s:
            f.write(b"\x0b ")  # spacer
            f.write(md5.encode())  # md5

    logger.info("[INFO] - MD5 to DB conversion successful")