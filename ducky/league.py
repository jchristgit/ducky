from typing import Self

from riotwatcher import LolWatcher, RiotWatcher


REGION_TO_PLATFORM = {
    "br": "br1",
    "eune": "eun1",
    "euw": "euw1",
    "jp": "jp1",
    "kr": "kr",
    "lan": "la1",
    "las": "la2",
    "na": "na1",
    "oce": "oc1",
    "tr": "tr1",
    "ru": "ru",
    "ph": "ph2",
    "sg": "sg2",
    "th": "th2",
    "tw": "tw2",
    "vn": "vn2",
}


PLATFORM_TO_REGION = {
    platform: region
    for region, platform in REGION_TO_PLATFORM.items()
}


def region_to_platform(region: str) -> str | None:
    return REGION_TO_PLATFORM.get(region.casefold())


def platform_to_region(platform: str) -> str | None:
    return PLATFORM_TO_REGION.get(platform.casefold()).upper()


class LolApi:
    def __init__(self, lol_watcher: LolWatcher, riot_watcher: RiotWatcher) -> None:
        self._lol_watcher = lol_watcher
        self._riot_watcher = riot_watcher

    @classmethod
    def from_api_key(cls, riot_api_key: str) -> Self:
        lol_watcher = LolWatcher(riot_api_key)
        riot_watcher = RiotWatcher(riot_api_key)
        return cls(lol_watcher=lol_watcher, riot_watcher=riot_watcher)

    def account_puuid(self, name: str, tagline: str) -> str:
        account = self._riot_watcher.account.by_riot_id("europe", name, tagline)
        return account["puuid"]

    def champion_mastery(self, region_or_platform: str, puuid: str, champion_id: int) -> dict:
        platform = region_to_platform(region_or_platform.casefold())
        if platform is None:
            platform = region_or_platform
        return self._lol_watcher.champion_mastery.by_puuid_by_champion(platform, puuid, champion_id)

