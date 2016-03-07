"""
Command line interface commands, available in this app.
"""

import argparse

from sunhead.cli.abc import Command

from aeroport import management


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


class Process(Command):
    """
    Callable for run processing of one origin of one airline
    """

    def handler(self, options) -> None:
        """Run collecting data"""
        print(options)
        print("test ok")

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
