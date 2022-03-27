import os
import json
import time
import shutil
import logging
import functools
import threading
import contextlib

from pathlib import Path
from typing import Any, Callable

# Constants
JSON = dict[str, Any]

logger = logging.getLogger(__name__)

class Settings:
    # Default output file data
    collection_name: str = "collection"
    collection_path: Path = Path(".").resolve(strict=True)
    modified_last: float = time.time()

    # Default actions for self modification
    rename_collection: bool = False
    move_current_collection: bool = False
    
    # Default actions when parsing file
    ignore_invalid_map_ids: bool = False
    ignore_invalid_set_ids: bool = False

    def __init__(self, *args, **kwargs) -> None:
        super(Settings, self).__init__(*args, **kwargs)

    def save(self) -> None:
        """Basic method to handle serialization of the class."""
        self.modified_last = time.time()
        with open("../settings.json", "w", encoding="utf8") as f:
            json.dump(self.__dict__, f, indent=4)

            logger.info("[[FILE I/O]] - settings.json saved")

    def load(self) -> None:
        """Basic method to deserialize a saved JSON."""
        with open("../settings.json", "wr", encoding="utf8") as f:
            settings = json.load(f)

        for k, v in settings.items():
            setattr(self, k, v)

        logger.info("[[FILE I/O]] - settings.json loaded")

    def get(self) -> JSON:
        """Basic method to get a dictionary of the current settings."""
        if time.time() - os.stat("../settings.json").st_mtime == self.modified_last:
            self.load()

            logger.info("[[FILE I/O]] - settings.json loaded")

        return self.__dict__

    def set_collection_name(
                            self,
                            name: str, 
                            rename_collection: bool | None = None
                        ) -> None:
        """Method to set the name of the generated collection.

        Parameters
        ----------
        name : str
            Name to use when generating collections
        rename_collection : bool | None, optional
            Rename the previously generated collection, if found, by default None
        """
        if rename_collection or self.rename_collection:
            with contextlib.suppress(FileNotFoundError):
                os.rename(
                            self.collection_path / f"{self.collection_name}.db",
                            self.collection_path / f"{name}.db"
                )

                logger.info(f"[[FILE I/O]] - {self.collection_name}.db renamed to {name}.db")
        
        self.collection_name = name
        
        logger.info(f"[[SETTINGS]] - collection_name changed to: {name}")

    def set_collection_path(
                            self,
                            path: os.PathLike | str, 
                            move_current_collection: bool = False
                        ) -> None:
        """Method to set the path of the generated collection.

        Parameters
        ----------
        path : os.PathLike | str
            Path to use when generating collections
        move_current_collection : bool, optional
            Move the collection to the new path, by default False
        """
        path = Path(path).resolve(strict=True)

        if move_current_collection or self.move_current_collection:
            with contextlib.suppress(FileNotFoundError):
                shutil.move(
                    self.collection_path / f"{self.collection_name}.db",
                    path / f"{self.collection_name}.db"
                )

                logger.info(f"[[FILE I/O]] - {self.collection_name}.db moved to {path}")

        self.collection_path = path

        logger.info(f"[[SETTINGS]] - collection_path changed to: {path}")

    def user_set_collection_name(self) -> None:
        """User-friendly method to set the name of the collection."""
        try:
            collection_name = None
            while (collection_name := input("Enter new collection name: ")).isalnum():
                print(f"Invalid collection name (Must be alphanumeric): {collection_name}")

            self.set_collection_name(collection_name, self.rename_collection)

            self.save()
        
        except KeyboardInterrupt:
            return None


    def user_set_collection_path(self) -> None:
        """User-friendly method to set the path of the collection."""
        try:
            collection_path = None
            while collection_path is None:
                collection_path = Path(input("Enter new collection path: "))

                if not collection_path.is_dir:
                    collection_path = None
                    continue

                try:
                    collection_path = collection_path.resolve(strict=True)
                
                except FileNotFoundError:
                    if required_input(f"{collection_path} not found, create new dir?: ", {'y', 'n'}) == "y":
                        collection_path.mkdir(exist_ok=True)
                        collection_path.resolve(strict=True)
                    
                    else:
                        collection_path = None
                        continue

            self.set_collection_path(collection_path, self.move_current_collection)

            self.save()

        except KeyboardInterrupt:
            return None

    def user_set_rename_collection(self) -> None:
        """User-friendly method to set if the previously generated collection should be renamed."""
        user_input = required_input("Rename collection?: [y/n]", {"y", "n"}).lower()
        
        try:
            self.rename_collection = user_input == "y"
            self.save()

        except KeyboardInterrupt:
            return None

    def user_set_move_current_collection(self) -> None:
        """User-friendly method to set if the previously generated collection should be moved."""
        user_input = required_input("Move current collection?: [y/n]", {"y", "n"}).lower()

        try:
            self.move_current_collection = user_input == "y"
            self.save()

        except KeyboardInterrupt:
            return None

    def user_set_ignore_invalid_map_ids(self) -> None:
        """User-friendly method to set if invalid map IDs should be ignored."""
        user_input = required_input("Ignore invalid map IDs?: [y/n]", {"y", "n"}).lower()

        try:
            self.ignore_invalid_map_ids = user_input == "y"
            self.save()

        except KeyboardInterrupt:
            return None

    def user_set_ignore_invalid_set_ids(self) -> None:
        """User-friendly method to set if invalid set IDs should be ignored."""
        user_input = required_input("Ignore invalid set IDs?: [y/n]", {"y", "n"}).lower()

        try:
            self.ignore_invalid_set_ids = user_input == "y"
            self.save()

        except KeyboardInterrupt:
            return None

    collection_path = data["output_collection_path"]

    # Removes extension if needed
    if output_collection_name.endswith(".db"):  # or ...
        output_collection_name = output_collection_name.replace(".db", "")

    # noinspection PyUnusedLocal
    user_input = None
    while (user_input := input("Rename current collection? (y/n): ")) not in ('y', 'n'):
        print(f"Invalid input: {user_input}")

    if user_input == 'y':
        os.rename(Path(collection_path).joinpath(data["output_collection_name"] + ".db"),
                  Path(collection_path).joinpath(output_collection_name + ".db"))

    with open("../settings.json", "w") as f:
        data["output_collection_name"] = output_collection_name
        json.dump(data, f, indent=4)

    logger.info(f"output_collection_name changed to: {output_collection_name}")


# TODO should ask if user wants to create new dir
def change_default_collection_output_path() -> None:
    output_collection_path = input("Enter new collection path: ")

    with open("../settings.json", "r") as f:
        data = json.load(f)

    collection_name = data["output_collection_name"]

    if not Path(output_collection_path).is_dir():
        print(f"Invalid dir: {output_collection_path}")
        return

    try:
        Path(output_collection_path + collection_name)

    except(OSError, RuntimeError):
        pass

    finally:
        # noinspection PyUnusedLocal
        user_input = None
        while (user_input := input("Move current collection to new Path? (y/n): ")) not in ('y', 'n'):
            print(f"Invalid input: {user_input}")

        if user_input == 'y':
            shutil.move(Path(data["output_collection_path"]).joinpath(collection_name + ".db"),
                        Path(output_collection_path).joinpath(collection_name + ".db"))

    with open("../settings.json", "w") as f:
        data["output_collection_path"] = output_collection_path
        json.dump(data, f, indent=4)

    logger.info(f"output_collection_path changed to: {output_collection_path}")
