import click

from heal.cli import extract, validate


@click.group()
def main():
    """HEAL Command Line Interface"""
    pass


@click.group()
def vlmd():
    """Commands for VLMD"""
    pass


vlmd.add_command(extract.extract)
vlmd.add_command(validate.validate)
