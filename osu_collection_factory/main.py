import os
import logging

from string import Template
from dotenv import load_dotenv

import util
import api_sentry
import md5_conversion
import osu_link_parser
import osu_collector_dumper


# Starts logger
logging.basicConfig(format="[%(levelname)s] - %(asctime)s - %(name)s:\n%(message)s",
                    datefmt="%d-%b-%y %H:%M:%S",
                    filename="../log.txt",
                    filemode="w",
                    level=logging.INFO)
logging.info("Starting logging")

# Loads .env file for osu!api key if stored
load_dotenv()

main_menu = """\r
osu! Collection Factory
----------------------------------------
1) Create collection from osu!collector
2) Create collection from file
3) Change Factory settings
4) Quit
"""

settings_menu = Template("""\r
Settings
---------------------
1) Change output collection name: Current name - $collection_name
2) Change output collection path: Current path - $collection_path
3) Rename last generated collection on collection name change?: $rename_collection
4) Move last generated collection to new path on collection path change?: $move_current_collection
5) Ignore invalid map IDs? : $ignore_invalid_map_ids
6) Ignore invalid set IDs? : $ignore_invalid_set_ids
7) Back
""")


def main(s: util.Settings | None = None, api: api_sentry.ApiSentry | None = None):
    """'Main' user-friendly function to assist with navigation.

    Parameters
    ----------
    s : util.Settings | None, optional
        Default settings to use, creates new instance if None, by default None
    api : api_sentry.ApiSentry | None, optional
        Default api sentry to use, creates new instance if None, by default None
    """
    osu_id = os.getenv("ID")
    osu_secret = os.getenv("SECRET")

    if osu_id is not None and osu_secret is not None:
        api = api_sentry.ApiSentry(osu_id, osu_secret)
        
    else:
        api = api_sentry.ApiSentry()
        api.manual_osu_user_authentication()

    s = util.Settings()
    s.load()

    print(main_menu)
    match util.required_input(
            input_message="> ",
            possible_options = {1, 2, 3, 4},
            verification_method=int
        ):
        case 1:
            osu_collector = osu_collector_dumper.OsuCollectorDump(s, api)

            osu_collector.user_set_id()

            if util.required_input(
                    input_message="Use a filter? [y/n]: ",
                    possible_options = {"y", "n"}
            ) == "y":
                osu_collector.user_set_filter()
                osu_collector.user_get_dump_with_filter()

            else:
                osu_collector.get_dump()

            osu_collector.log_ids()

            # TODO this allows for flexibility if we want to allow dumping of multiple collections into 1 
            # (/different collections in the .db/etc)

            md5_conversion.convert_md5s_to_db(s=s, md5s=list(osu_collector.md5s))

        case 2:
            file_path = None

            parser = osu_link_parser.ParseOsuLinksFromFile(s=s, api=api)

            while True:
                try:
                    file_path = input("Enter file path (default-./list.txt): ")

                    parser.set_current_file(file_path)
                    break

                except FileNotFoundError:
                    print(f"Invalid file path: {file_path}")

            parser.parse_plaintext()

            md5_conversion.convert_md5s_to_db(s=s, md5s=list(parser.md5s))

        case 3:
            s = settings(s)

        case 4:
            quit(0)

        case _:
            quit(1)

    main(s, api)


def settings(s: util.Settings | None = None) -> util.Settings:
    """User-friendly function to see and set the Factory's settings.

    Parameters
    ----------
    s : util.Settings | None, optional
        Settings to use, creates new instance if None, by default None

    Returns
    -------
    util.Settings
        Returns current settings
    """
    if s is None:
        s = util.Settings()

    s_dict = s.get()

    print(
        settings_menu.substitute(
            collection_name=s_dict["collection_name"],
            collection_path=s_dict["collection_path"],
            rename_collection=s_dict["rename_collection"],
            move_current_collection=s_dict["move_current_collection"],
            ignore_invalid_map_ids=s_dict["ignore_invalid_map_ids"],
            ignore_invalid_set_ids=s_dict["ignore_invalid_set_ids"]
        )
    )
    try:
        match util.required_input(
            input_message="> ",
            possible_options = {i for i in range(7)},
            verification_method=int
            ):
            case 1:
                s.user_set_collection_name()

            case 2:
                s.user_set_collection_path()

            case 3:
                s.user_set_rename_collection()

            case 4:
                s.user_set_move_current_collection()
            
            case 5:
                s.user_set_ignore_invalid_map_ids()

            case 6:
                s.user_set_ignore_invalid_set_ids()

            case 7:
                return s

            case _:
                quit(1)

    except KeyboardInterrupt:
        main()

    return settings(s)

if __name__ == "__main__":
    main()
