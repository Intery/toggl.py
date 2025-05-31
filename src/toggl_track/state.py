from collections import defaultdict
from typing import TYPE_CHECKING, NamedTuple

from .http import TrackHTTPClient

from .models import Workspace, Project, TimeEntry, Client, Tag


class WorkspaceChildren(NamedTuple):
    projects: set[int]
    entries: set[int]
    clients: set[int]
    tags: set[int]


class TrackState:
    """
    Holds the state of a Toggl Track client session.
    """

    def __init__(self, http: TrackHTTPClient):
        self.http = http

        # Map of worspace_id -> Workspace
        self.workspaces = {}

        # Map of project_id -> Project
        self.projects = {}

        # Map of entry_id -> TimeEntry
        self.time_entries = {}

        # Map of client_id -> Client
        self.clients = {}

        # Map of tag_id -> Tag
        self.tags = {}

        self.workspace_children = defaultdict(lambda: WorkspaceChildren(set(), set(), set(), set()))

    # Access methods for session state

    def get_workspace(self, wid: int):
        return self.workspaces.get(wid, None)

    def get_workspace_projects(self, wid: int) -> list[Project]:
        if wid not in self.workspaces:
            raise ValueError(f"Workspace {wid} not found.")
        pids = self.workspace_children[wid].projects
        return [self.projects[pid] for pid in pids if pid in self.projects]

    def get_workspace_entries(self, wid: int) -> list[TimeEntry]:
        if wid not in self.workspaces:
            raise ValueError(f"Workspace {wid} not found.")
        tids = self.workspace_children[wid].entries
        return [self.time_entries[tid] for tid in tids if tid in self.time_entries]

    def get_workspace_tags(self, wid: int) -> list[Tag]:
        if wid not in self.workspaces:
            raise ValueError(f"Workspace {wid} not found.")
        tids = self.workspace_children[wid].tags
        return [self.tags[tid] for tid in tids if tid in self.tags]

    def get_workspace_clients(self, wid: int) -> list[Client]:
        if wid not in self.workspaces:
            raise ValueError(f"Workspace {wid} not found.")
        cids = self.workspace_children[wid].clients
        return [self.clients[cid] for cid in cids if cid in self.clients]

    def get_project(self, pid: int):
        return self.projects.get(pid, None)

    def get_client(self, cid: int):
        return self.clients.get(cid, None)

    def get_entry(self, eid: int):
        return self.time_entries.get(eid, None)

    def get_tag(self, tid: int):
        return self.tags.get(tid, None)

    # Data loading from HTTP and webhook payloads

    def recursive_load_data(self, payload):
        # TODO: This is nonsense, fix
        # Also logging
        for wspace_data in payload.get('workspaces', []) or []:
            self.add_workspace_data(wspace_data)

        # Extract clients
        for client_data in payload.get('clients', []) or []:
            self.add_client_data(client_data)

        # Extract tags
        for tag_data in payload.get('tags', []) or []:
            if not isinstance(tag_data, str):
                self.add_tag_data(tag_data)

        # Extract projects
        for project_data in payload.get('projects', []) or []:
            self.add_project_data(project_data)

        # Extract time entries
        for entry_data in payload.get('time_entries', []) or []:
            self.add_entry_data(entry_data)

    def add_workspace_data(self, payload):
        wspace = Workspace.from_data(payload, state=self)
        self.workspaces[wspace.id] = wspace
        self.recursive_load_data(payload)

    def add_project_data(self, payload):
        project = Project.from_data(payload, state=self)
        self.projects[project.id] = project
        self.workspace_children[project.workspace_id].projects.add(project.id)
        self.recursive_load_data(payload)
        return project

    def add_entry_data(self, payload):
        entry = TimeEntry.from_data(payload, state=self)
        self.time_entries[entry.id] = entry
        self.workspace_children[entry.workspace_id].entries.add(entry.id)
        self.recursive_load_data(payload)
        return entry

    def add_client_data(self, payload):
        client = Client.from_data(payload, state=self)
        self.clients[client.id] = client
        self.workspace_children[client.workspace_id].clients.add(client.id)
        self.recursive_load_data(payload)
        return client

    def add_tag_data(self, payload):
        print(payload)
        tag = Tag.from_data(payload, state=self)
        self.tags[tag.id] = tag
        self.workspace_children[tag.workspace_id].tags.add(tag.id)
        # Tags are the only model where we are sure we will not get other models embedded
        return tag
