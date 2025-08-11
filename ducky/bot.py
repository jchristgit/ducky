from discord.ext.commands import Bot

from .mastery_role import MasteryRole
from .mastery_table import MasteryTable
from .league import LolApi


class CommandBot(Bot):
    def __init__(self, *args, **kwargs) -> None:
        self._dsn = kwargs.pop('dsn')
        self._riot_api_key = kwargs.pop('riot_api_key')
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        lol_api = LolApi.from_api_key(self._riot_api_key)
        await self.add_cog(MasteryRole(dsn=self._dsn, lol_api=lol_api))
        await self.add_cog(MasteryTable(dsn=self._dsn, lol_api=lol_api))
