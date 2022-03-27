import os
import re
import logging

from pathlib import Path

import util 
import api_sentry

# TODO locally cache set_id -> map_id -> md5

logger = logging.getLogger(__name__)


class ParseOsuLinksFromFile:
    def __init__(self, s: util.Settings, api: api_sentry.ApiSentry, *args, **kwargs):
        super(ParseOsuLinksFromFile, self).__init__(*args, **kwargs)

        self.settings = s
        self.api = api

        self.current_file = Path.cwd() / "list.txt"

        self.set_ids = set()
        self.map_ids = set()
        self.md5s = set()

        # Regex pattern to pull set IDs if no map ID is specified
        self.set_id_pattern = re.compile(
            r"((?!(?<=ets/)\d{1,7}(#|%23))((?<=s/)\d{1,7}))"
        )
        
        # Regex pattern to pull map IDs
        self.map_id_pattern = re.compile(
            r"(((?<!ets/)(?<!/s/)(?<=\w/)\d{1,8}|^\d{1,8}))"
        )

        # Regex pattern to pull osu.ppy.sh/s/* links
        self.osu_link_pattern = re.compile(
            r"(((http.{0,4})?osu\.ppy\.sh/(?!u)\w{1,11}/((\d{1,8})?((#|%23)\w"
            r"{1,5}/\d{1,8}|\w{1,7}\?b=\d{1,8}(&m=\d)?)|\d{1,8}))|(^\d{1,8}))"
        )

        if not self.api.osu_authenticated:
            self.api.authenticate_osu()

    def reset_current_file(self):
        self.current_file = Path.cwd() / "list.txt"

    def set_current_file(self, file: Path | str | None = None):
        if file is None or file == "":
            self.current_file = Path.cwd() / "list.txt"

        else:
            try:
                self.current_file = Path(file).resolve(strict=True)

            except (RuntimeError, OSError):
                message = f"[ERROR] : Invalid path given: {file}"
                
                logger.error(message)
                raise FileNotFoundError(message)

    def parse_plaintext(self, file: Path | str | None = None):
        if file is not None and file != "":
            self.set_current_file(file)
        
        elif file == "":
            self.reset_current_file()

        self.parse_ids_from_plaintext_file()
        self.set_ids_to_map_ids()
        self.map_ids_to_md5s()

        return self.md5s

    def parse_ids_from_plaintext_file(self, file: Path | str | None = None):
        if file is not None and file != "":
            self.set_current_file(file)

        elif file == "":
            self.reset_current_file()
            
        with open(self.current_file, "r", encoding='utf8') as f:
            f_lines = f.read()

        for link in self.osu_link_pattern.finditer(f_lines):
            set_id = re.search(self.set_id_pattern, link.group(0))

            # Only append if set ID is found without map ID
            if set_id is not None:
                logger.info(f"[INFO] : Possible set ID found: {set_id.group(0)}")
                self.set_ids.add(set_id.group(0))
                continue

            map_id = re.search(self.map_id_pattern, link.group(0))

            # Only append if map ID is found
            if map_id is not None:
                logger.info(f"[INFO] : Possible map ID found: {map_id.group(0)}")
                self.map_ids.add(map_id.group(0))

            else:
                logger.warning(f"[WARNING] : Invalid link?: {link.group(0)}")

    # TODO cache downloads
    # Writes all map IDs from set ID to list.txt
    def set_ids_to_map_ids(self):
        # TODO MULTITHREAD THIS!!
        for set_id in self.set_ids:
            try:
                beatmaps = self.api.get_beatmaps_from_set_id(set_id)
            
            except Exception as e:
                if self.settings.ignore_invalid_set_ids:
                    continue

                raise e

            beatmap_ids = []
            for beatmap in beatmaps:
                beatmap_id = beatmap.get("beatmap_id")

                if beatmap_id is not None:
                    beatmap_ids.append(beatmap_id)

                elif not beatmap_id:
                    logger.warning(f"Beatmap set {set_id}: returned with an invalid id")

            for item in beatmap_ids:
                self.map_ids.add(item)

            logger.info(f"Set ID - {set_id}:\n - {beatmap_ids}")

    def map_ids_to_md5s(self):
        beatmaps = self.api.get_beatmaps_from_map_ids(list(self.map_ids))

        for beatmap in beatmaps:
            self.md5s.add(beatmap["file_md5"])
