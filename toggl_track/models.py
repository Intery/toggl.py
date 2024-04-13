import datetime as dt
from typing import Any, Optional, TYPE_CHECKING

from attrs import define, field, Factory, validators, converters, NOTHING

from .lib import utc_now

if TYPE_CHECKING:
    from .state import TrackState


# Custom converters and validators
def dt_from_timestamp(timestamp: str) -> dt.datetime:
    ts = dt.datetime.fromisoformat(timestamp)
    if ts.tzinfo is None:
        ts.replace(tzinfo=dt.timezone.utc)
    return ts


# Helper methods for constructing fields
PREMIUM = 'premium'

def model_field(
    default=NOTHING, validator=None, repr=True,
    eq=True, order=None, hash=None, init=True, metadata=None,
    converter=None,
    premium=False
):
    metadata = metadata or {}
    metadata[PREMIUM] = premium

    return field(
        default=default, validator=validator, repr=repr,
        eq=eq, order=order, hash=hash, init=init,
        metadata=metadata, converter=converter,
    )

dt_field_args = {
    'validator': validators.instance_of(dt.datetime),
    'converter': dt_from_timestamp
}

opt_dt_field_args = {
    'validator': validators.instance_of((type(None), dt.datetime)),
    'converter': converters.optional(dt_from_timestamp),
    'default': None,
}

    

@define
class TrackModel:
    """
    ABC for all Toggl Track Models.
    """
    state: Optional['TrackState'] = field()

    @classmethod
    def from_data(cls, payload: dict, state=None):
        # TODO: Some nicer way of filtering these
        # Also a way that supports aliases
        attrs = {attr.name for attr in cls.__attrs_attrs__}
        return cls(
            **{key: value for key, value in payload.items() if key in attrs},
            state=state
        )

    def update_data(self, payload):
        raise NotImplementedError


class _Workspaced:
    state: Optional['TrackClient']
    workspace_id: int

    @property
    def workspace(self):
        if self.state is None:
            raise ValueError(f"Cannot fetch workspace on stateless {self.__class__.__name__}")
        return self.state.get_workspace(self.workspace_id)


@define(kw_only=True)
class Tag(TrackModel, _Workspaced):
    # Tag ID
    id: int = field(validator=validators.instance_of(int))

    # Name of the tag
    name: str = field(validator=validators.instance_of(str))

    # When Tag was last modified
    at: dt.datetime = field(**dt_field_args)

    # ID of user who created the tag
    creator_id: int = field(validator=validators.instance_of(int))

    # ID of the workspace this tag belongs to
    workspace_id: int = field(validator=validators.instance_of(int))

    # Undocumented
    permissions: Optional[str] = field()

    # When the tag was deleted if applicable.
    deleted_at: Optional[dt.datetime] = field(**opt_dt_field_args)


@define(kw_only=True)
class ProjectUser(TrackModel, _Workspaced):
    # Project user id
    id: int = field(validator=validators.instance_of(int))

    # When Project User was last modified
    at: dt.datetime = field(**dt_field_args)

    # Project id
    project_id: int = field(validator=validators.instance_of(int))

    # User id
    user_id: int = field(validator=validators.instance_of(int))

    # Group id
    group_id: int = field(validator=validators.instance_of(int))

    # Labour cost
    labour_cost: int = field(validator=validators.instance_of(int))

    # Whether user is a manager of the project
    manager: bool = field(validator=validators.instance_of(bool))

    # Workspace id
    workspace_id: int = field(validator=validators.instance_of(int))

    # Custom rate for project user
    rate: Optional[float] = field(default=None)

    # When the rate was last updated
    rate_last_updated: Optional[dt.datetime] = field(**opt_dt_field_args)


# TODO: Add an explicit premium metadata tag to the premium fields?
# Would make verification simpler


@define(kw_only=True)
class Project(TrackModel, _Workspaced):
    # ID of the project
    id: int = field(validator=validators.instance_of(int))

    # Whether the project is active or archived
    active: bool = field(validator=validators.instance_of(bool))

    # Colour of the project
    color: str = field(validator=validators.instance_of(str))

    # Actual hours
    actual_hours: Optional[int] = None

    # Actual seconds
    actual_seconds: Optional[int] = None

    # When project was last modified
    at: dt.datetime = field(**dt_field_args)

    # Whether the project is private
    is_private: bool = field(validator=validators.instance_of(bool))

    # Name of the project
    name: str = field(validator=validators.instance_of(str))

    # ID of the client for the project
    client_id: Optional[int] = None

    @property
    def client(self):
        if self.state is None:
            raise ValueError(f"Cannot fetch client on stateless {self.__class__.__name__}")
        if self.client_id is None:
            return None
        return self.state.get_client(self.client_id)

    @property
    def colour(self) -> str:
        return self.color

    # When the project was created
    created_at: dt.datetime = field(**dt_field_args)

    # When the project ends
    end_date: Optional[dt.datetime] = field(
        **opt_dt_field_args
    )

    # Permissions?
    permissions: Optional[str] = None

    # Sever deletion date?
    server_deleted_at: Optional[dt.datetime] = field(
        **opt_dt_field_args
    )

    # Start date of the project
    start_date: Optional[dt.datetime] = field(
        **opt_dt_field_args
    )

    # Status of the project
    # TODO: Should be an enum
    status: str

    # Workspace ID
    workspace_id: int

    # (Premium) Whether estimates are based on task hours
    auto_estimates: Optional[bool] = None

    # (Premium) Whether project is billable
    billable: Optional[bool] = None

    # (Premium) Whether the project is a template
    template: Optional[bool] = None
    template_id: Optional[int] = None

    # (Premium) Hourly rate
    rate: Optional[int] = None

    # (Premium) When the rate last changed
    rate_last_updated: Optional[dt.datetime] = field(
        **opt_dt_field_args
    )

    # (Premium) Whether the project is recurring
    recurring: Optional[bool] = None
    recurring_parameters: Optional[Any] = None

    # (Premium) Estimated time
    estimated_hours: Optional[int] = None
    estimated_seconds: Optional[int] = None

    # (Premium) Fixed fee
    fixed_fee: Optional[int] = None

    # (Premium) Currency the rate is in
    currency: Optional[str] = None

    # (Premium) Current project period
    current_period: Optional[Any] = None


# TODO: Incomplete models:


@define(kw_only=True)
class TimeEntry(TrackModel, _Workspaced):
    # When time entry was last modified
    at: dt.datetime = field(**dt_field_args)

    # (Premium) Whether time entry is billable
    billable: Optional[bool] = None

    # Entry Description
    # May be None if not provided on creation
    description: Optional[str] = None

    # Duration
    # Raw value will be negative for ongoing entries
    duration: int

    @property
    def actual_duration(self):
        if self.running:
            return self.duration
        else:
            return (utc_now() - self.start).total_seconds()

    @property
    def running(self):
        return (self.duration > 0)

    # Time Entry ID
    id: int = field(validator=validators.instance_of(int))

    # Permissions?
    permissions: Optional[str] = None

    # Project id
    # May be None if time entry has no project
    project_id: Optional[int] = None

    @property
    def project(self) -> Optional[Project]:
        if self.state is None:
            raise ValueError(f"Cannot fetch project on stateless {self.__class__.__name__}")
        if self.project_id is None:
            return None
        return self.state.get_project(self.project_id)

    # TODO: Finish field implementations

    start: dt.datetime = field(**dt_field_args)
    stop: Optional[dt.datetime] = field(**opt_dt_field_args)
    tag_ids: list[int] = Factory(list)
    tags: list[str] = Factory(list)

    # Workspace id
    workspace_id: int = field(validator=validators.instance_of(int))


# Workspaces
@define(kw_only=True)
class Workspace(TrackModel):
    admin: bool

    # When workspace was last modified
    at: dt.datetime = field(**dt_field_args)

    # Workspace ID
    id: int = field(validator=validators.instance_of(int))


# User profile
@define(kw_only=True)
class Profile(TrackModel):
    at: dt.datetime = field(**dt_field_args)

    # User ID
    id: int = field(validator=validators.instance_of(int))

    default_workspace_id: int

    timezone: str

    updated_at: dt.datetime = field(**dt_field_args)


# Client
@define(kw_only=True)
class Client(TrackModel):
    archived: bool
    at: dt.datetime = field(**dt_field_args)
    id: int = field(validator=validators.instance_of(int))
    name: str
    wid: int

    @property
    def workspace_id(self):
        return self.wid
