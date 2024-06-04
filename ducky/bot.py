from discord.ext.commands import Bot

from .error_handler import ErrorHandler
from .mastery_role import MasteryRole
from .mastery_table import MasteryTable


class CommandBot(Bot):
    def __init__(self, *args, **kwargs):
        self._dsn = kwargs.pop('dsn')
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        await self.add_cog(MasteryRole(dsn=self._dsn))
        await self.add_cog(MasteryTable(dsn=self._dsn))
