import json
import logging
import asyncio
import aiohttp
from typing import Optional

from base64 import b64encode

from .errors import HTTPException, LoginFailure, NotFound, PaymentRequired
from .lib import slow_lock

logger = logging.getLogger(__name__)


class Route:
    BASE = 'https://api.track.toggl.com/api/v9/'

    def __init__(self, method, path, **parameters):
        self.path = path
        self.method = method

        url = self.BASE + self.path

        self.url = url.format(**parameters) if parameters else url


class AccountsRoute(Route):
    BASE = 'https://accounts.toggl.com/api/'


class TrackHTTPClient:
    """
    Static interface to the v9 Toggl Track restful API.
    """
    user_agent = "Toggl.py v2 written by Interitio (cona@thewisewolf.dev)"

    def __init__(self, user_agent=None, loop=None):
        if user_agent is not None:
            self.user_agent = user_agent

        self.loop = loop or asyncio.get_event_loop()
        self._lock = asyncio.Lock()

        self.authHeader: None | str = None  # Set upon login

        self.session: None | aiohttp.ClientSession = None

    async def close(self):
        if self.session:
            await self.session.close()

    async def request(self, route, static=True, data=None, **kwargs):
        if self.session is None or self.session.closed:
            raise ValueError("Session is closed or not started.")
        if not self.authHeader:
            raise ValueError("Cannot request before login.")

        if 'params' in kwargs:
            kwargs['params'] = {key: json.dumps(obj) for key, obj in kwargs['params'].items()}

        await self._lock.acquire()
        with slow_lock(self._lock, self.loop, 1):
            headers = {
                "Content-Type": "application/json",
                "Accept": "*/*",
                "User-Agent": self.user_agent,
            }
            if static:
                headers["Authorization"] = self.authHeader
            if data is not None:
                kwargs['data'] = json.dumps(data)

            logger.debug(
                f"Sending {route.method} request to {route.url}."
            )

            async with self.session.request(route.method, route.url, headers=headers, **kwargs) as resp:
                text = await resp.text(encoding='utf-8')

                logger.debug(
                    f"{route.url} response {resp.status}: {text}"
                )
                if 300 > resp.status >= 200:
                    # Okay response, parse and return
                    return json.loads(text)
                elif resp.status == 402:
                    raise PaymentRequired(resp, text)
                elif resp.status == 403:
                    raise LoginFailure
                elif resp.status == 404:
                    raise NotFound(resp, text)
                else:
                    raise HTTPException(resp, text)

    async def login(self, APIKey=None, username=None, password=None):
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = aiohttp.ClientSession()

        if APIKey:
            auth = f"{APIKey}:api_token"
        elif username and password:
            auth = f"{username}:{password}"
        else:
            raise ValueError("Insufficient credentials supplied for client authentication.")

        self.authHeader = "Basic " + b64encode(auth.encode()).decode("ascii").rstrip()

        # 'Log in' by getting the user profile
        return await self.get_my_profile()

    async def _login_cookie(self):
        """
        Authenticate and obtain a session cookie with the API.

        NOTE: This is now defunct in the v9 API
        since we can no longer get a session cookie with an api token.
        """
        try:
            await self.request(
                AccountsRoute('POST', 'sessions'),
                data="",
                static=True,
            )
        except HTTPException as e:
            if e.response.status == 403:
                raise LoginFailure("Improper credentials passed")
            else:
                raise

    # --------------------
    # Me Chapter
    # --------------------
    async def get_my_profile(self, with_related_data=False):
        params = {
            'with_related_data': with_related_data
        }

        return await self.request(Route('GET', 'me'), params=params)

    async def get_my_projects(self, include_archived: Optional[str] = None, since: Optional[int] = None):
        params = {}
        if include_archived is not None:
            params['include_archived'] = include_archived
        if since is not None:
            params['since'] = since

        return await self.request(Route('GET', 'me/projects'), params=params)

    # Get ProjectsPaginated

    async def get_my_tags(self, since: Optional[int] = None):
        params = {}
        if since is not None:
            params['since'] = since

        return await self.request(Route('GET', 'me/tags'), params=params)

    # Get Tasks

    # Get TrackReminders

    async def get_my_webtimer(self):
        return await self.request(Route('GET', 'me/web-timer'))

    async def get_my_workspaces(self, since: Optional[int] = None):
        params = {}
        if since is not None:
            params['since'] = since

        return await self.request(Route('GET', 'me/workspaces'), params=params)

    # --------------------
    # Preferences Chapter
    # --------------------

    async def get_my_preferences(self):
        return await self.request(Route('GET', 'me/preferences'))

    # Update my preferences

    # Get my preferences for a specific client

    # Update my preferences for a specific client

    # Get Workspace preferences

    # Update Workspace preferences

    # --------------------
    # Time Entries Chapter
    # --------------------

    # Get my time entries

    # Get current time entry
    async def get_current_entry(self):
        return await self.request(Route('GET', 'me/time_entries/current'))

    # Get my time entry by id

    # Create a new workspace time entry
    async def create_time_entry(self, workspace_id, meta=None, **kwargs):
        payload = kwargs
        payload.setdefault("created_with", self.user_agent)
        payload['workspace_id'] = workspace_id
        params = {'workspace_id': workspace_id}
        route = Route('POST', 'workspaces/{workspace_id}/time_entries', **params)
        query = {'meta': meta} if meta is not None else {}
        return await self.request(route, data=payload, params=query)


    # Bulk edit workspace time entries 

    # Update a single workspace time entry 

    # Delete a workspace time entry 

    # Stop a ws time entry 
    async def stop_entry(self, workspace_id, time_entry_id):
        params = {
            'workspace_id': workspace_id,
            'time_entry_id': time_entry_id,
        }
        return await self.request(
            Route('PATCH', 'workspaces/{workspace_id}/time_entries/{time_entry_id}/stop', **params)
        )


    # --------------------
    # Organizations Chapter
    # --------------------

    # --------------------
    # Workspace Chapter
    # --------------------

    # Create a workspace in an organization 

    # Get users in an organization in a workspace 

    # Update users in an organization in a workspace 

    # Edit a workspace (Post, but without a workspace id?)

    # Get a workspace by id

    # Update a workspace by id

    # Update workspace alerts?

    # Delete workspace alerts

    # Get workspace statistics

    # Get workspace time entry constraints (whether fields are required)

    # Get TrackReminders

    # Post TrackReminders

    # Put TrackReminder

    # Delete TrackReminder

    # Get Workspace users

    # Update workspace user (what you can update isn't given)

    # Request password change for workspace user

    # Put workspace user

    # Delete workspace user

    # --------------------
    # Clients Chapter
    # --------------------

    # Get clients in a workspace 

    # Create client in a workspace

    # Fetch a client from a wspace by id

    # (Put) Update a workspace client

    # Delete a wspace client

    # Archive wspace client

    # Restore client and optionally projects

    # --------------------
    # Projects Chapter
    # --------------------

    # Get the wspace project users 
    # Q: What's a project user?

    # Create a workspace project user

    # Update the list of wspace projects users 

    # Update a specific wspace project user

    # Delete a wspace project user

    # Get workspace projects

    # Create a workspace project

    # Bulk edit wspace projects (batch operations)

    # Get a wspace project by id

    # Edit a wspace project by id

    # Delete a wspace project

    # --------------------
    # Tasks Chapter
    # --------------------

    # --------------------
    # Tags Chapter
    # --------------------
    
    # Get workspace tags

    # Create workspace tag

    # Update a tag by id

    # Delete a tag

    # --------------------
    # Approvals Chapter
    # --------------------




