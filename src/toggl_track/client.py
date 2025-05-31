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
        self.state: TrackState = TrackState(self.http)

        self.profile: Optional[models.Profile] = None

    @property
    def default_workspace(self):
        if self.profile is None:
            raise ValueError("No default workspace before login.")
        return self.state.get_workspace(self.profile.default_workspace_id)

    async def close(self):
        await self.http.close()
        del self.state
        self.state = TrackState(self.http)
        self.profile = None

    async def login(self, *args, **kwargs):
        profile_data = await self.http.login(*args, **kwargs)
        self.profile = models.Profile.from_data(profile_data, state=self.state)

    async def sync(self, flush=True):
        state = TrackState(self.http) if flush else self.state

        data = await self.http.get_my_profile(with_related_data=True)
        self.profile = models.Profile.from_data(data, state=state)
        state.recursive_load_data(data)

        self.state = state

    async def fetch_current_entry(self) -> Optional[TimeEntry]:
        try:
            data = await self.http.get_current_entry()
            if data:
                entry = self.state.add_entry_data(data)
            else:
                entry = None
        except NotFound:
            entry = None
        return entry

    async def start_entry(self, workspace_id, description, start, project_id=None, tag_ids=[]) -> TimeEntry:
        create_args = {'description': description}
        create_args['start'] = start.isoformat()
        create_args['duration'] = -1
        if project_id:
            create_args['project_id'] = project_id
        if tag_ids:
            create_args['tag_ids'] = tag_ids
        data = await self.http.create_time_entry(workspace_id, **create_args)
        return self.state.add_entry_data(data)
