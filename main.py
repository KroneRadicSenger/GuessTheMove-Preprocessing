#!/usr/bin/env python

import click

from modules.commands.commands import analyze, annotate, api


@click.group()
def main():
    """
    Tool for analyzing chess games and annotating the output files with full player names and ELO ratings.
    """
    pass


main.add_command(analyze)
main.add_command(annotate)
main.add_command(api)

if __name__ == '__main__':
    main()
