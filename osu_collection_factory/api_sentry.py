import json
import time
import logging
import requests

from collections.abc import Mapping
from typing import Any, Literal, Sequence

import util

logger = logging.getLogger(__name__)

# TODO Test for bad input(s)
# TODO More api endpoints
class ApiSentry:
    token: str
    invalid_at: float
    start_time: float
    expires_int: float

    def __init__(
            self,
            client_id: int | str | None = None, 
            client_secret: str | None = None
        ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret

        self.starting = True
        self.start()

    @property
    def OSU_AUTHENTICATION_HEADER(self) -> dict[str, str]:
        """dict[str, str]: osu!api authentication header."""
        return {"Authorization": f"Bearer {self.token}"}

    def start(self) -> None:
        """Method that starts the sentry and authenticates the user."""
        self.starting = True
        
        self.token, self.expires_in = self.authenticate_osu()
        self.osu_authenticated = True
        self.invalid_at = time.time() + self.expires_in

        self.starting = False

    @util.limit(60, 60)
    def make_api_request(
            self,
            url: str,
            method: Literal["GET"] | Literal["POST"],
            osu_api_request: bool = True,
            headers: dict[str, Any] | None = None,
            payload: dict[str, Any] | None = None,
            catch_errors: Mapping[int, tuple[type[BaseException], str]] | None = None,
        ) -> util.JSON | list[util.JSON] | Any:
        """Ratelimited method (60 requests a minute) to make API requests.

        Parameters
        ----------
        url : str
            URL to use, if osu_api_request is True: url = "https://osu.ppy.sh/api/v2" + url
        method : Literal["GET"] | Literal["POST"]
            HTTP method to use in request
        osu_api_request : bool, optional
            Should the request be directed towards the osu! API? By default True
        headers : dict[str, Any] | None, optional
            Headers to use in HTTP request, by default None
        payload : dict[str, Any] | None, optional
            Payload to use in HTTP request, by default None
        catch_errors : Mapping[int, tuple[type[BaseException], str]] | None, optional
            HTTP errors, exceptions to raise and message to send if the HTTP error is raised, by default None

        Returns
        -------
        util.JSON | list[util.JSON] | Any
            The osu! API returns JSONs or a list of JSONs

        """
        r = None
        if osu_api_request and not self.starting and time.time() >= getattr(self, "invalid_at", -1):
            logger.info("[INFO] : osu! API Sentry (re)starting")
            self.start()

        if method not in ("GET", "POST"):
            message = f"[CRITICAL] : INVALID HTTP METHOD RECEIVED: {method}"

            logger.critical(message)
            raise NotImplementedError(message)

        api_access_url = "https://osu.ppy.sh/api/v2/" if osu_api_request else ""

        try:
            if method == "GET":
                r = requests.get(
                    url=api_access_url+url,
                    headers=headers,
                    params=payload
                )

            elif method == "POST":
                r = requests.post(
                    url=url, 
                    headers=headers, 
                    data=payload
                )

            else:
                message = f"[CRITICAL] : INVALID HTTP METHOD RECEIVED (SHOULD NOT BE REACHED): {method}"
                
                logger.critical(message)
                raise NotImplementedError(message)

            r.raise_for_status()

            data = r.json()

        except requests.HTTPError as e:
            if catch_errors is not None:
                response = e.response.status_code

                possible_error = catch_errors.get(response)
                if possible_error is not None:

                    exception, message = possible_error

                    logger.error(f"[ERROR HTTP] : Exception raised: {exception}\n{message = }\n{response = }")
                    raise exception(message, response)
                
            raise e

        except json.JSONDecodeError:
            if isinstance(r, requests.Response):
                raise requests.HTTPError(
                    f"[ERROR HTTP] : Bad JSON received - {r.raw}", 
                    422
                )
        
            message = "[CRITICAL] : UNKNOWN OBJECT RETURNED"
            
            logger.critical(message)
            raise NotImplementedError(message)

        return data

    # Client authentication
    def authenticate_osu(self) -> tuple[str, int]:
        """Method to authenticate osu API requests.

        Returns
        -------
        tuple[str, int]
            Returns the authentication token and the time it expires in
        """
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "public",
        }

        errors = {404: (requests.HTTPError, "[HTTP ERROR] : User not found")}

        data = self.make_api_request(
            url="https://osu.ppy.sh/oauth/token",
            method="POST",
            osu_api_request=False,
            payload=payload,
            catch_errors=errors,
        )

        if isinstance(data, list):
            data = data[0]

        token = data.get("access_token")
        token_type = data.get("token_type")
        expires_in = data.get("expires_in")

        if token is None or token_type is None or expires_in is None:
            data = f"Token: {token}\nToken Type: {token_type}\nExpires_in: {expires_in}"
            raise requests.HTTPError(
                f"[ERROR - HTTP] : Bad data received:\n{data}",
                422,
            )

        elif data.get("access_token") == 0:
            raise requests.HTTPError("[ERROR - AUTHENTICATION] : Token expired", 401)

        return token, expires_in

    def get_recent_activity(
            self,
            user: int, 
            limit: int | None = None, 
            offset: int | None = None
        ) -> list[util.JSON]:
        """Method to get the recent activity for user.

        Parameters
        ----------
        user : int
            ID of the user
        limit : int | None, optional
            Limit of activities to receive, by default None
        offset : int | None, optional
            Offset of the recent activities to start at, by default None

        Returns
        -------
        list[util.JSON]
            Returns a list of recent activities
        """
        payload = {"limit": limit, "offset": offset}
        errors = {404: (requests.HTTPError, "[HTTP ERROR] : User not found")}

        return self.make_api_request(
            url=f"users/{user}/recent_activity",
            method="GET",
            headers=self.OSU_AUTHENTICATION_HEADER,
            payload=payload,
            catch_errors=errors
        )

    def get_recent_plays(
            self, 
            user: int, 
            limit: int | None = None, 
            include_fails: bool = True
        ) -> list[util.JSON]:
        """Method to get the recent plays of a user.

        Parameters
        ----------
        user : int
            ID of the user
        limit : int | None, optional
            Limit of plays to receive, by default None
        include_fails : bool, optional
            Include fails in recent plays, by default True

        Returns
        -------
        list[util.JSON]
            Returns a list of recent plays
        """
        payload = {"limit": limit, "include_fails": int(include_fails)}
        errors = {404: (requests.HTTPError, "[HTTP ERROR] : User not found")}

        return self.make_api_request(
            url=f"users/{user}/scores/recent",
            method="GET",
            headers=self.OSU_AUTHENTICATION_HEADER,
            payload=payload,
            catch_errors=errors
        )

    def get_beatmap_from_map_id(
            self,
            map_id: int
        ) -> util.JSON:  # sourcery skip: class-extract-method
        """Method to get beatmap from a map ID

        Returns
        -------
        util.JSON
            
        """
        payload = {"id": map_id}
        errors = {}
        
        return self.make_api_request(
            url="beatmap",
            method="GET",
            headers=self.OSU_AUTHENTICATION_HEADER,
            payload=payload,
            catch_errors=errors
        )

    def get_beatmaps_from_map_ids(
            self, 
            map_ids: Sequence[int],
        ) -> list[util.JSON]:
        """Method to get beatmaps from multiple map ids.

        Parameters
        ----------
        map_ids : Sequence[int]
            A sequence of map IDs to use

        Returns
        -------
        list[util.JSON]
            Returns a list of beatmaps
        """
        errors = {}  # TODO find.

        maps = []
        ids_left = len(map_ids)
        map_ids = list(map_ids)
        
        iteration = 0
        while ids_left > 0:
            payload = {"ids[]": map_ids[iteration*50:iteration*50+50]}
            maps.append(
                self.make_api_request(
                    url="beatmaps",
                    method="GET",
                    headers=self.OSU_AUTHENTICATION_HEADER,
                    payload=payload,
                    catch_errors=errors
                )
            )
            ids_left -= 50
            iteration += 1

        return maps

    def get_beatmaps_from_set_id(
            self,
            set_id: int,
    ) -> list[util.JSON]:
        """Method to get beatmaps from a set ID.

        Parameters
        ----------
        set_id : int
            The set ID

        Returns
        -------
        list[util.JSON]
            Returns a list of beatmaps
        """
        payload = {"id": set_id}
        errors = {}

        return self.make_api_request(
            url="beatmapsets",
            method="GET",
            headers=self.OSU_AUTHENTICATION_HEADER,
            payload=payload,
            catch_errors=errors
        )

    # TODO See if there's a way to use chrome driver/set this up properly
    def manual_osu_user_authentication(self):
        """User-friendly method to authenticate the user to make requests to the osu! API."""
        self.client_id = util.required_input("Enter client id: ", verification_method=int)
        self.client_id = input("Enter client secret: ")

        self.authenticate_osu()
        
