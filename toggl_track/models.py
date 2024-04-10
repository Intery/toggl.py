from abc import ABC
import datetime as dt
from typing import Any, Optional, TYPE_CHECKING

from attrs import define, field, Factory, validators, converters

if TYPE_CHECKING:
    from .client import TogglTrackClient


def dt_from_timestamp(timestamp: str) -> dt.datetime:
    ts = dt.datetime.fromisoformat(timestamp)
    if ts.tzinfo is None:
        ts.replace(tzinfo=dt.timezone.utc)
    return ts
    

@define
class TogglTrackModel:
    """
    ABC for all Toggl Track Models.
    """
    state: Any = field()

    @classmethod
    def from_data(cls, payload: dict, state=None):
        # TODO: Some nicer way of filtering these
        attrs = {attr.name for attr in cls.__attrs_attrs__}
        return cls(
            **{key: value for key, value in payload.items() if key in attrs},
            state=state
        )

    def update_data(self, payload):
        raise NotImplementedError


class _Workspaced:
    state: Optional['TogglTrackClient']
    workspace_id: int

    @property
    def workspace(self):
        if self.state is None:
            raise ValueError(f"Cannot fetch workspace on stateless {self.__class__.__name__}")
        return self.state.get_workspace(self.workspace_id)


@define(kw_only=True)
class Tag(TogglTrackModel, _Workspaced):
    # Tag ID
    id: int = field(validator=validators.instance_of(int))

    # Name of the tag
    name: str = field(validator=validators.instance_of(str))

    # When Tag was last modified
    at: dt.datetime = field(
        validator=validators.instance_of(dt.datetime),
        converter=dt_from_timestamp
    )

    # ID of user who created the tag
    creator_id: int = field(validator=validators.instance_of(int))

    # Undocumented
    permissions: Optional[str] = field()

    # ID of the workspace this tag belongs to
    workspace_id: int = field(validator=validators.instance_of(int))

    # When the tag was deleted if applicable.
    deleted_at: Optional[dt.datetime] = field(
        validator=validators.instance_of((type(None), dt.datetime)),
        converter=converters.optional(dt_from_timestamp),
        default=None,
    )


@define(kw_only=True)
class ProjectUser(TogglTrackModel, _Workspaced):
    # TODO: Clean this up
    # When Project User was last modified
    at: dt.datetime = field(
        validator=validators.instance_of(dt.datetime),
        converter=dt_from_timestamp
    )

    # Project id
    project_id: int = field(validator=validators.instance_of(int))

    # Project user id
    id: int = field(validator=validators.instance_of(int))

    # Group id
    group_id: int = field(validator=validators.instance_of(int))

    # Labour cost
    labour_cost: int = field(validator=validators.instance_of(int))

    # Whether user is a manager of the project
    manager: bool = field(validator=validators.instance_of(bool))

    # User id
    user_id: int = field(validator=validators.instance_of(int))

    # Workspace id
    workspace_id: int = field(validator=validators.instance_of(int))

    # Custom rate for project user
    rate: Optional[float] = field(default=None)

    # When the rate was last updated
    rate_last_updated: Optional[dt.datetime] = field(
        validator=validators.instance_of((type(None), dt.datetime)),
        converter=converters.optional(dt_from_timestamp),
        default=None,
    )


# TODO: Add an explicit premium metadata tag to the premium fields?
# Would make verification simpler


@define(kw_only=True)
class Project(TogglTrackModel, _Workspaced):
    # Whether the project is active or archived
    active: bool

    # Actual hours
    actual_hours: Optional[int] = None

    # Actual seconds
    actual_seconds: Optional[int] = None

    # When project was last modified
    at: dt.datetime = field(
        validator=validators.instance_of(dt.datetime),
        converter=dt_from_timestamp
    )

    # (Premium) Whether estimates are based on task hours
    auto_estimates: Optional[bool] = None

    # (Premium) Whether project is billable
    billable: Optional[bool] = None

    # ID of the client for the project
    client_id: Optional[int] = None

    @property
    def client(self):
        if self.state is None:
            raise ValueError(f"Cannot fetch client on stateless {self.__class__.__name__}")
        if self.client_id is None:
            return None
        return self.state.get_workspace(self.client_id)

    # Colour of the project
    color: str

    @property
    def colour(self) -> str:
        return self.color

    # When the project was created
    created_at: dt.datetime = field(
        validator=validators.instance_of(dt.datetime),
        converter=dt_from_timestamp
    )

    # (Premium) Currency the rate is in
    currency: Optional[str] = None

    # (Premium) Current project period
    current_period: Optional[Any] = None

    # When the project ends
    end_date: Optional[dt.datetime] = field(
        validator=validators.instance_of((type(None), dt.datetime)),
        converter=converters.optional(dt_from_timestamp),
        default=None,
    )

    # (Premium) Estimated time
    estimated_hours: Optional[int] = None
    estimated_seconds: Optional[int] = None

    # (Premium) Fixed fee
    fixed_fee: Optional[int] = None

    # ID of the project
    id: int

    # Whether the project is private
    is_private: bool

    # Name of the project
    name: str

    # Permissions?
    permissions: Optional[str] = None

    # (Premium) Hourly rate
    rate: Optional[int] = None

    # (Premium) When the rate last changed
    rate_last_updated: Optional[dt.datetime] = field(
        validator=validators.instance_of((type(None), dt.datetime)),
        converter=converters.optional(dt_from_timestamp),
        default=None,
    )

    # (Premium) Whether the project is recurring
    recurring: Optional[bool] = None
    recurring_parameters: Optional[Any] = None

    # Sever deletion date?
    server_deleted_at: Optional[dt.datetime] = field(
        validator=validators.instance_of((type(None), dt.datetime)),
        converter=converters.optional(dt_from_timestamp),
        default=None,
    )

    # Start date of the project
    start_date: Optional[dt.datetime] = field(
        validator=validators.instance_of((type(None), dt.datetime)),
        converter=converters.optional(dt_from_timestamp),
        default=None,
    )

    # Status of the project
    # TODO: Should be an enum
    status: str

    # (Premium) Whether the project is a template
    template: Optional[bool] = None
    template_id: Optional[int] = None

    # Workspace ID
    workspace_id: int
