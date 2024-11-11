import click
import logging

import cdislogging
import heal.cli.extract as extract
import heal.cli.validate as validate
import heal.cli.vlmd as vlmd

# import heal


@click.group()
@click.option("--version", is_flag=True, default=False, help="Show HEAL-SDK Version")
@click.pass_context
def main(ctx, version):
    """HEAL-Platform SDK Command Line Interface"""
    ctx.ensure_object(dict)

    if version:
        click.echo("0.1.1.")
        exit()


main.add_command(vlmd.vlmd)
# main.add_command(extract.extract)
# main.add_command(validate.validate)

if __name__ == "__main__":
    main()
