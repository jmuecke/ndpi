import click

from ndpi.cli.tshark import tshark


@click.group()
def cli():
    """ndpi command line tools"""


cli.add_command(tshark)


if __name__ == "__main__":
    cli()
