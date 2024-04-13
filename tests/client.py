import asyncio
import logging
import toml

from .context import toggl_track

from toggl_track.client import TrackClient


async def main():
    config = toml.load('tests/config.toml')
    client = TrackClient()
    await client.login(APIKey=config['toggl']['apikey'])
    await client.sync()
    logging.info(f"Logged in as {client.profile.id} in {client.profile.timezone}")
    logging.info(f"{len(client.state.projects)} Projects, {len(client.state.time_entries)} Time Entries")


if __name__ == '__main__':
    asyncio.run(main())
