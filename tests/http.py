import asyncio
import logging

import toml

from .context import toggl_track

from toggl_track.errors import HTTPException, LoginFailure
from toggl_track.http import TrackHTTPClient

# Move to model tests
from toggl_track.models import Tag, Project

async def login(apikey: str):
    logging.info("Testing HTTPClient login with APIKey")

    logging.info("Initialising Client")
    client = TrackHTTPClient()

    logging.info("Logging In")
    try:
        await client.login(APIKey=apikey)
    except LoginFailure:
        logging.exception("Login failed with LoginFailure.")
        raise
    except HTTPException:
        logging.exception("Login failed with HTTPException.")
        raise
    except Exception:
        logging.exception("Login failed with unknown exception.")
        raise

    logging.info("Testing /me request.")
    await client.get_my_profile()

    logging.info("Logged in successfully.")

    return client


async def test_my_endpoints(client: TrackHTTPClient):
    logging.info("Testing /me endpoints.")

    # logging.info("Requesting Projects.")
    # await client.get_my_projects()

    # await client.get_my_webtimer()
    await client.get_my_workspaces()

    logging.info("Testing /me endpoints complete.")


async def test_tags_static(client: TrackHTTPClient):
    logging.info("Testing static object loading.")

    # logging.info("Testing Tags")
    # TODO: Use fixtures for this instead of dynamically loading
    # raw_tags = await client.get_my_tags()
    # tags = [Tag.from_data(raw) for raw in raw_tags]
    # print('\n'.join(repr(tag) for tag in tags))

    logging.info("Testing Projects")
    raw_projects = await client.get_my_projects()
    for raw in raw_projects:
        try:
            project = Project.from_data(raw)
        except Exception:
            print(raw)
            raise
        print(project)



async def main():
    logging.info("Loading Configuration")
    config = toml.load('tests/config.toml')

    logging.info("Starting Tests")
    client = await login(config['toggl']['apikey'])
    # await test_my_endpoints(client)

    await test_tags_static(client)

    logging.info("Tests Complete")
    await client.close()


if __name__ == '__main__':
    asyncio.run(main())
