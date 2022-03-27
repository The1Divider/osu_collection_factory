import logging

from typing import Literal

import util
import api_sentry

logger = logging.getLogger(__name__)

filter_menu = """\r
1) By star rating
2) By bpm
"""

class OsuCollectorDump:
    collection_id: int | None

    min_sr_filter: float | None
    max_sr_filter: float | None

    min_bpm_filter: float | None
    max_bpm_filter: float | None

    filter_for_dump: Literal["bpm"] | Literal["difficulty_rating"]


    def __init__(self, s: util.Settings, api: api_sentry.ApiSentry, *args, **kwargs):
        super(OsuCollectorDump, self).__init__(*args, **kwargs)

        self.settings = s
        self.api = api

        self.md5s = set()
        self.beatmap_ids = set()

    @property
    def url(self) -> str:
        """str: The url for the osu!collector collection"""
        if self.collection_id is not None:
            return f"https://osucollector.com/api/collections/{self.collection_id}"
            
        else:
            raise NotImplementedError

    # TODO cache this
    def log_ids(self) -> None:
        """Logs recieved beatmaps"""
        for i, j in zip(self.beatmap_ids, self.md5s):
            logger.info(f"[INFO] - Dumped id: {i} - md5: {j}")
        logger.info("[INFO] - Collected successfully\n")

    def user_set_filter(self) -> None:
        """User-friendly method to set the filter used for the dump."""
        self.filter_for_dump=util.required_input(
            input_message="Choose filter: ",
            possible_options={"bpm", "difficulty_rating"},
            invalid_input_message="Invalid filter (bpm/difficulty_rating): "
        )

    def get_dump(self):
        """Method to get the osu!collector dump."""
        logger.info(f"[INFO] - Collecting beatmaps from osu!Collector collection id: {self.collection_id}")

        collection = self.api.make_api_request(
            url=self.url,
            method="GET", 
            osu_api_request=False
        )

        if isinstance(collection, list):
            collection = collection[0]

        # Collect beatmap ids and checksums from the json
        for beatmap_set in collection["beatmapsets"]:
            for beatmap in beatmap_set["beatmaps"]:
                self.beatmap_ids.add(str(beatmap["id"]))
                self.md5s.add(beatmap["checksum"])

    def get_dump_with_filter(self):
        """Method to get the osu!collector dump for a given filter."""
        has_more = True
        cursor = "0"

        url = f"{self.url}/beatmapsv2?"

        filter_dict = {
            "bpm": {
                "name": "bpm",
                "min": self.min_bpm_filter, 
                "max": self.max_bpm_filter
            },
            "difficulty_rating": {
                "name": "star rating",
                "min": self.min_sr_filter,
                "max": self.max_sr_filter
            }
        }

        logger.info(f"[INFO] - Collecting beatmaps from osu!Collector collection {self.collection_id}:")

        logger.info(f"[INFO] - Using {filter_dict[self.filter_for_dump]['name']}: {filter_dict[self.filter_for_dump]['min']} -> {filter_dict[self.filter_for_dump]['max']}")

        while has_more:        
            payload = {
                "cursor": cursor,
                "perPage": "100",
                "sortBy": self.filter_for_dump,
                "filterMin": filter_dict[self.filter_for_dump]["min"],
                "filterMax": filter_dict[self.filter_for_dump]["max"]
            }

            collection = self.api.make_api_request(url=url, method="GET", payload=payload, osu_api_request=False)
            
            if isinstance(collection, list):
                collection = collection[0]

            # Collect beatmap ids and checksums from the json
            for beatmap in collection["beatmaps"]:
                self.beatmap_ids.add(beatmap["url"].split("/")[-1])
                self.md5s.add(beatmap["checksum"])

            # Log ids
            # TODO cache instead
            for i, j in zip(self.beatmap_ids, self.md5s):
                logger.info(f"[INFO] - Dumped id: {i} - md5: {j}")

            # If more is available to request
            has_more = collection["hasMore"]
            if has_more:
                cursor = collection["nextPageCursor"]

                logger.info(f"[INFO] - Next cursor: {cursor}")

        logger.info("Collected successfully\n")

    def user_get_dump_with_filter(self):
        """User-friendly method to get a osu!collector dump with a filter."""
        match self.filter_for_dump:
            case "difficulty_rating":
                self.min_sr_filter, self.max_sr_filter = util.sorted_filter_verification("sr")
                self.using_sr_filter = True

            case "bpm":
                self.min_bpm_filter, self.max_bpm_filter = util.sorted_filter_verification("BPM")
                self.using_bpm_filter = True

            case _:
                raise NotImplementedError

        self.get_dump_with_filter()
    
    def user_set_id(self) -> None:
        """User-friendly method to set the ID of the collection to dump."""
        while True:
            collection_id = input("Enter osu!collector collection ID or URL: ").split("/")[-1]
            try:
                self.collection_id = int(collection_id)
                break

            except ValueError:
                print(f"Invalid ID or url: {collection_id}")
