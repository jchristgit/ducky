import argparse
import logging
import os

import cassiopeia
from discord import Intents

from .bot import CommandBot


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
    intents = Intents.default()
    intents.message_content = True
    intents.members = True
    bot = CommandBot(dsn=args.dsn, command_prefix=args.prefix,
                     intents=intents, description=__doc__, max_messages=None)
    print("starting up")
    bot.run(args.token)


if __name__ == '__main__':
    main()
