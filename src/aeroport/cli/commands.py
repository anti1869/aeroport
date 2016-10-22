"""
Command line interface commands, available in this app.
"""

import argparse
import asyncio
from typing import Any

from sunhead.cli.abc import Command


class RunInLoopMixin(object):

    def run_in_loop(self, coro) -> Any:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(coro)
        return result


class InitDB(Command):
    """
    Create tables and stuff.
    """

    def handler(self, options) -> None:
        """Drop and create tables"""
        from aeroport.db import create_tables, drop_tables, get_all_models
        all_models = get_all_models()
        names = set(options["tables"].lower().split(","))
        selected_models = all_models if options["tables"].lower() == "all" \
            else tuple(filter(lambda x: x.__name__.lower() in names, all_models))

        drop_tables(models=selected_models)
        create_tables(models=selected_models)

    def get_parser(self):
        parser_command = argparse.ArgumentParser(description=self.handler.__doc__)
        parser_command.add_argument(
            "tables",
            type=str,
            help="Tables to recreate (comma separated, ALL=all)",
        )
        return parser_command


class Airlines(Command):
    """
    List airlines, registered with this aeroport installation.
    """

    def handler(self, options) -> None:
        """Print list of registered airlines"""

        from aeroport.management.utils import get_airlines_list
        for airline in get_airlines_list():
            print("{} ({})".format(airline.name, airline.module_path))

    def get_parser(self):
        return super().get_parser()


class Origins(Command):
    """
    List origins for one specific airline.
    """

    def handler(self, options) -> None:
        """Print list of origins, available in airline"""

        # TODO: Graceful error exceptions here
        from aeroport.management.utils import get_airline
        airline = get_airline(options["airline"])
        for origin in airline.get_origin_list():
            print("{} {} ({})".format(airline.name, origin.name, origin.module_path))

    def get_parser(self):
        parser_command = argparse.ArgumentParser(description=self.handler.__doc__)
        parser_command.add_argument(
            "airline",
            type=str,
            help="Which airline is print origins for",
        )
        return parser_command


class Process(RunInLoopMixin, Command):
    """
    Callable for run processing of one origin of one airline
    """

    def handler(self, options) -> None:
        """Run collecting data"""

        # TODO: Set destination here
        # TODO: Better DB handling

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._handler(options))

    async def _handler(self, options):
        from aeroport.dispatch import process_origin, ProcessingException

        try:
            await process_origin(
                options["airline"], options["origin"], options.get("destination"), use_await=True
            )
        except ProcessingException:
            quit(-1)

    def get_parser(self):
        parser_command = argparse.ArgumentParser(description=self.handler.__doc__)
        parser_command.add_argument(
            "airline",
            type=str,
            help="Which airline is print origins for",
        )
        parser_command.add_argument(
            "origin",
            type=str,
            help="Which origin to process",
        )
        parser_command.add_argument(
            "-d",
            dest="destination",
            type=str,
            help="Specific destination",
        )
        parser_command.add_argument(
            "-t",
            dest="target",
            type=str,
            help="Specific destination target role",
        )
        return parser_command
