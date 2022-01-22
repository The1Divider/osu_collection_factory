import logging

from typing import Any

from util import get_json_response


logger = logging.getLogger(__name__)


# Writes all map IDs from set ID to list.txt
def set_id_list_to_map_id_list(set_ids: set, api_key: str) -> set:
    url = "https://osu.ppy.sh/api/get_beatmaps"
    ids = set()

    for set_id in set_ids:
        payload = {
            'k': api_key,
            's': set_id,
            'limit': 100,
        }

        beatmap_json: dict[str | Any] | None = None
        try:
            beatmap_json = get_json_response(url, payload)
        except Exception as e:
            logger.exception(e)

            print(f"An error occurred: {e}")
            print(f"Create db from {len(ids)} md5s? (y/n)")

            # noinspection PyUnusedLocal
            user_input = None
            while (user_input := input()) not in ("y", "n"):
                print(f"Invalid input: {user_input}")

            if user_input == "y":
                return ids

            else:
                quit(1)

        if beatmap_json is None or beatmap_json == []:
            logger.warning(f"Set ID: {set_id} is invalid")

        beatmap_ids = []
        for beatmap in beatmap_json:
            beatmap_id = beatmap.get("beatmap_id")

            if beatmap_id is not None:
                beatmap_ids.append(beatmap_id)

            elif not beatmap_id:
                logger.warning(f"Beatmap set {set_id}: returned with an invalid id")

        for item in beatmap_ids:
            ids.add(item)

        logger.info(f"Set ID - {set_id}:\n - {beatmap_ids}")

    return ids
