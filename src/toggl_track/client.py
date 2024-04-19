from typing import Optional

from toggl_track.errors import NotFound
from .http import TrackHTTPClient
from .state import TrackState
from . import models

from .models import TimeEntry


class TrackClient:
    """
    Represents a connection to the Track API
    on behalf of a single user.
    """

    def __init__(self):
        self.http: TrackHTTPClient = TrackHTTPClient()
        self.state: TrackState = TrackState()

        self.profile: Optional[models.Profile] = None

    @property
    def default_workspace(self):
        if self.profile is None:
            raise ValueError("No default workspace before login.")
        return self.state.get_workspace(self.profile.default_workspace_id)

    async def close(self):
        await self.http.close()
        del self.state
        self.state = TrackState()
        self.profile = None

    async def login(self, *args, **kwargs):
        profile_data = await self.http.login(*args, **kwargs)
        self.profile = models.Profile.from_data(profile_data, state=self.state)

    async def sync(self, flush=True):
        state = TrackState() if flush else self.state

        data = await self.http.get_my_profile(with_related_data=True)
        self.profile = models.Profile.from_data(data, state=state)

        # Extract workspaces
        for wspace_data in data.get('workspaces', []):
            wspace = models.Workspace.from_data(wspace_data, state=state)
            state.add_workspace(wspace)

        # Extract clients
        for client_data in data.get('clients', []):
            client = models.Client.from_data(client_data, state=state)
            state.add_client(client)

        # Extract tags
        for tag_data in data.get('tags', []):
            tag = models.Tag.from_data(tag_data, state=state)
            state.add_tag(tag)

        # Extract projects
        for project_data in data.get('projects', []):
            project = models.Project.from_data(project_data, state=state)
            state.add_project(project)

        # Extract time entries
        for entry_data in data.get('time_entries', []):
            entry = models.TimeEntry.from_data(entry_data, state=state)
            state.add_entry(entry)

        self.state = state

    async def fetch_current_entry(self) -> Optional[TimeEntry]:
        try:
            data = await self.http.get_current_entry()
            entry = TimeEntry.from_data(data, self.state)
            self.state.add_entry(entry)
        except NotFound:
            entry = None
        return entry
