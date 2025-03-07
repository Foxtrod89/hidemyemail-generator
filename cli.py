#!/usr/bin/env python3
import asyncio
import click
from main import generate, list, delete, deactivate, reactivate, cookie_writer

@click.group()
def cli():
    pass

@click.command()
@click.option("--count", default=1, help="How many emails to generate", type=int)
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
@click.option("--search", default=None, help="Search emails by label")
def listcommand(active, search):
    "List emails"
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(list(active, search, label="", notes=""))
    except KeyboardInterrupt:
        pass

@click.command()
@click.argument("emails", nargs=-1)
@click.option('--file', type=click.File('r'), help="to delete emails from file")
def deletecommand(emails, file):
    "Remove emails"
    if emails:
        try:
            asyncio.run(delete(emails))
        except KeyboardInterrupt:
            pass
    elif file:
        try:
           asyncio.run(delete(file))
        except KeyboardInterrupt:
            pass
    else:
        click.echo('No emails provided.')

@click.command()
@click.argument("emails", nargs=-1)
@click.option('--file', type=click.File('r'), help="to deactivate emails from file")
def deactivatecommand(emails, file):
    "Deactivate emails"
    if emails:
        try:
            asyncio.run(deactivate(emails))
        except KeyboardInterrupt:
            pass
    elif file:
        try:
           asyncio.run(deactivate(file))
        except KeyboardInterrupt:
            pass
    else:
        click.echo('No emails provided.')

@click.command()
@click.argument("emails", nargs=-1)
@click.option('--file', type=click.File('r'), help="to reactivate emails from file")
def reactivatecommand(emails, file):
    "Reactivate emails"
    if emails:
        try:
            asyncio.run(reactivate(emails))
        except KeyboardInterrupt:
            pass
    elif file:
        try:
           asyncio.run(reactivate(file))
        except KeyboardInterrupt:
            pass
    else:
        click.echo('No emails provided.')



@click.command()
@click.option(
                "--browser",
                default='safari', 
                required = False, 
                type=click.Choice(['chrome','safari','firefox'],
                case_sensitive=False))
def extract_cookies(browser: str):
    "To extract cookies from browser(Chrome, Safari and Firefox)"
    cookie_writer(browser)

cli.add_command(listcommand, name="list")
cli.add_command(generatecommand, name="generate")
cli.add_command(deletecommand, name = "delete")
cli.add_command(deactivatecommand, name = "deactivate")
cli.add_command(reactivatecommand, name = "reactivate")
cli.add_command(extract_cookies, name="extract")

if __name__ == "__main__":
    cli()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(generate(None, label="", notes=""))
    except KeyboardInterrupt:
        pass
