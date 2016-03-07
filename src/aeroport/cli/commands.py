"""
Command line interface commands, available in this app.
"""

import argparse
import asyncio
from typing import Any

from sunhead.cli.abc import Command

from aeroport import management


class RunInLoopMixin(object):

    def run_in_loop(self, coro) -> Any:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(coro)
        return result



class Airlines(Command):
    """
    List airlines, registered with this aeroport installation.
    """

    def handler(self, options) -> None:
        """Print list of registered airlines"""

        for airline in management.get_airlines_list():
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

        airline = management.get_airline(options["airline"])
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
        airline = management.get_airline(options["airline"])
        origin = airline.get_origin(options["origin"])

        # TODO: Set destination here

        self.run_in_loop(origin.process())

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
