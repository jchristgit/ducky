import asyncio

from cassiopeia import Account, Region, Summoner


def as_region(value: str) -> Region:
    return Region(value.upper())


async def user_input_to_summoner(region: Region, name_with_tagline: str) -> Summoner:
    name, tagline = name_with_tagline.split("#")
    account = Account(name=name, tagline=tagline, region=region)
    summoner = await asyncio.get_event_loop().run_in_executor(
        None, lambda: account.summoner
    )  # noblock event loop
    return summoner
