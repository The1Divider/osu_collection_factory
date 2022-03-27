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

def required_input(
                    input_message: str,
                    possible_options: set | None = None,
                    verification_method: Callable[[str], Any] | None = None,
                    invalid_input_message: str | None = None
                ) -> Any:
    """Utility loop to get a required input from the user.

    Parameters
    ----------
    input_message : str
        Prompt to display
    possible_options : set | None, optional
        Set containing all accepted input options, by default None
    verification_method : Callable[[str], Any] | None, optional
        Function or method to verify the input against, by default None
    invalid_input_message : str | None, optional
        Prompt to display if input is invalid, by default None
        (defaults to f"Invalid input: {user_input}")

    Returns
    -------
    Any
        The user's accepted input
    """
    # noinspection PyUnusedLocal
    user_input = None
    while user_input is None:
        try:   
            user_input = input(input_message)

            if verification_method is not None:
                try:
                    user_input = verification_method(user_input)

                except NameError as e:
                    logger.critical(f"[CRITICAL] - INVALID VERFICATION METHOD: {verification_method}")
                    logger.info("[INFO] - Verfication method must be of type Callable[[str], Any]")

            if possible_options is not None:
                while user_input not in possible_options:
                    print(
                        "Invalid input: {user_input}"
                    ) if invalid_input_message is None else invalid_input_message + user_input

                    user_input = input(user_input)


        except Exception as e:
            logger.warning("[WARNING] - User input caused the following exception:")
            logger.exception(f"[EXCEPTION] - {e}")
            print(f"Invalid input: {user_input}" if invalid_input_message is None else f"{invalid_input_message}{user_input}")

            user_input = None

    return user_input

# https://github.com/enricobacis/limit
def limit(limit, every=1):
    """This decorator factory creates a decorator that can be applied to
    functions in order to limit the rate the function can be invoked.
    The rate is `limit` over `every`, where limit is the number of
    invocation allowed every `every` seconds.
    limit(4, 60) creates a decorator that limit the function calls
    to 4 per minute. If not specified, every defaults to 1 second."""

    def limit_decorator(fn):
        """This is the actual decorator that performs the rate-limiting."""
        semaphore = threading.Semaphore(limit)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            semaphore.acquire()

            try:
                return fn(*args, **kwargs)

            finally:  # ensure semaphore release
                timer = threading.Timer(every, semaphore.release)
                timer.setDaemon(True)  # allows the timer to be canceled on exit
                timer.start()

        return wrapper

    return limit_decorator

def sorted_filter_verification(filter_name: str) -> tuple[float, float]:
    """Verify values for filters with ranges.

    Parameters
    ----------
    filter_name : str
        Name of the filter being used.

    Returns
    -------
    tuple[float, float]
        Min and max values.
    """
    min_input, max_input = None, None
    while min_input is None or max_input is None:
        if min_input is None:
            min_input = required_input(
                input_message=f"Min {filter_name}: ",
                verification_method=float, 
                invalid_input_message="Invalid min (Must be a positive decimal number): "
            )

            if min_input >= 0:
                min_input = None
                print(f"Invalid {filter_name} (Must be positive): {min_input}")
                continue
        
        if max_input is None:
            max_input = required_input(
                input_message=f"Max {filter_name}: ",
                verification_method=float, 
                invalid_input_message="Invalid max (Must be a positive decimal number): "
            )

            if max_input >= 0:
                max_input = None
                print(f"Invalid {filter_name} (Must be positive): {max_input}")
                continue
        
        break
    

    return min_input, max_input