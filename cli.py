#!/usr/bin/env python3

import asyncio
import click

from main import generate
from main import list

@click.group()
def cli():
    pass

@click.command()
@click.option(
    "--count", default=1, help="How many emails to generate", type=int
)
@click.option("--label", required=True, help="To set custom label")
@click.option("--notes", required=False, help="To set custom notes")
def generatecommand(count: int, label:str, notes: str):
    "Generate emails"
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(generate(count, label, notes))
    except KeyboardInterrupt:
        pass

@click.command()
@click.option(
    "--active/--inactive", default=True, help="Filter Active / Inactive emails"
)
@click.option("--search", default=None, help="Search emails")
def listcommand(active, search):
    "List emails"
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(list(active, search, label="", notes=""))
    except KeyboardInterrupt:
        pass

cli.add_command(listcommand, name="list")
cli.add_command(generatecommand, name="generate")

if __name__ == "__main__":
    cli()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(generate(None, label="", notes=""))
    except KeyboardInterrupt:
        pass
