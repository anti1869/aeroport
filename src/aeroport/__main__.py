"""
Entry point for the application.
"""

from sunhead.cli.commands.runserver import Runserver
from sunhead.cli.entrypoint import main as sunhead_main

from aeroport.cli.commands import Airlines, Origins, Process


commands = (
    Runserver("aeroport.web.server.AeroportHTTPServer"),
    Airlines(),
    Origins(),
    Process(),
)


DEFAULT_ENVIRONMENT_VARIABLE = "AEROPORT_SETTINGS_MODULE"
GLOBAL_CONFIG_MODULE = "aeroport.settings.base"


def main():
    sunhead_main(
        commands=commands,
        settings_ennvar=DEFAULT_ENVIRONMENT_VARIABLE,
        fallback_settings_module=GLOBAL_CONFIG_MODULE
    )


if __name__ == '__main__':
    main()
