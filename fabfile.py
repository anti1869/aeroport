"""
Deploying with CI to production-like environment to see and test it in action.
This is for my development. Probably, you don't need this.
"""

from contextlib import contextmanager
import os

from fabric.api import task, cd, run, env, local, put, prefix, sudo, warn_only, lcd, local


AEROPORT_PROD_HOST = os.environ.get("AEROPORT_PROD_HOST", None)


# Environment settings
env.roledefs = {
    'production': {
        'hosts': [AEROPORT_PROD_HOST],  # quick hack for test CI
        'activate': 'pyenv activate aeroport',
        'settings': 'aeroport.settings.base',
    },
}


def get_setting(setting_name):
    """
    Get setting name from the roles dictionary.
    """
    setting = None
    try:
        setting = env.roledefs[env['effective_roles'][0]][setting_name]
    except IndexError:
        print("No role specified. Use ``fab -R <role> <command>`` syntax.")
        quit(-1)
    return setting


@contextmanager
def virtualenv():
    """
    Context manager for remote virtualenv activating
    """
    with prefix(get_setting('activate')):
        yield


@task
def restart_app_server():
    run("pyenv activate circus && circusctl restart aeroport")


@task
def deploy_app():
    """
    Deploy main application to it's server.

    :param quickfix: If true, will build quickfix package.
    :param checks: If True, will run safety checks before doing anything.
    """
    print("Deploying app")
    with virtualenv():
        run("pip install -U -qq aeroport")
        # run("manage.py migrate --settings={}".format(get_setting('settings')))

    restart_app_server()


@task
def deploy():
    """
    Main deployment routine, that makes full deployment cycle to production.
    """
    if not AEROPORT_PROD_HOST:
        print("Set AEROPORT_PROD_HOST variable")
        quit(-1)

    deploy_app()
