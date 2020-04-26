import argparse
import logging
import os

import cassiopeia
from discord.ext.commands import Bot

from .error_handler import ErrorHandler
from .mastery_role import MasteryRole
from .mastery_table import MasteryTable


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,)
    parser.add_argument(
        '-p',
        '--prefix',
        help="command prefix [$PREFIX]",
        default=os.getenv('PREFIX', '+'),
    )
    parser.add_argument(
        '-d',
        '--dsn',
        help="database connection string [$DSN]",
        default=os.getenv('DSN'),
    )
    parser.add_argument(
        '-k', '--api-key', help="riot API key [$API_KEY]", default=os.getenv('API_KEY'),
    )
    parser.add_argument(
        '-t', '--token', help="bot token [$TOKEN]", default=os.getenv('TOKEN'),
    )
    return parser


def main() -> None:
    args = create_parser().parse_args()
    cassiopeia.apply_settings({'logging': {'print_calls': False}})
    cassiopeia.set_riot_api_key(args.api_key)
    bot = Bot(command_prefix=args.prefix, description=__doc__)
    print("starting up")
    bot.add_cog(ErrorHandler())
    bot.add_cog(MasteryRole(dsn=args.dsn))
    bot.add_cog(MasteryTable(dsn=args.dsn))
    bot.run(args.token)


if __name__ == '__main__':
    main()
