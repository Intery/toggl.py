from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Workspace, Project, TimeEntry, Client, Tag


class TrackState:
    """
    Holds the state of a Toggl Track client session.

    TODO:
        Partial Objects
    """

    def __init__(self):
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

        # Map of workspace_id -> {project_id}
        self.workspace_projects = defaultdict(set)

        # Map of workspace_id -> {entry_id}
        self.workspace_entries = defaultdict(set)

        # Map of workspace_id -> {client_id}
        self.workspace_clients = defaultdict(set)

        # Map of workspace_id -> {tag_id}
        self.workspace_tags = defaultdict(set)

    def get_workspace(self, wid: int):
        return self.workspaces.get(wid, None)

    def get_project(self, pid: int):
        return self.projects.get(pid, None)

    def get_client(self, cid: int):
        return self.clients.get(cid, None)

    def get_entry(self, eid: int):
        return self.time_entries.get(eid, None)

    def get_tag(self, tid: int):
        return self.tags.get(tid, None)

    def add_workspace(self, wspace: 'Workspace'):
        self.workspaces[wspace.id] = wspace

    def add_project(self, project: 'Project'):
        self.workspace_projects[project.workspace_id].add(project.id)
        self.projects[project.id] = project

    def add_entry(self, entry: 'TimeEntry'):
        self.workspace_entries[entry.workspace_id].add(entry.id)
        self.time_entries[entry.id] = entry

    def add_client(self, client: 'Client'):
        self.workspace_clients[client.workspace_id].add(client.id)
        self.clients[client.id] = client

    def add_tag(self, tag: 'Tag'):
        self.workspace_tags[tag.workspace_id].add(tag.id)
        self.tags[tag.id] = tag
