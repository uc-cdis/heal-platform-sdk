import logging

import cdislogging
import click

import heal.cli.vlmd as vlmd


@click.group()
@click.option(
    "--silent",
    "silent",
    is_flag=True,
    default=False,
    help="don't show ANY logs",
)
@click.pass_context
def main(ctx, silent):
    """HEAL-Platform SDK Command Line Interface"""
    ctx.ensure_object(dict)

    if silent:
        # we still need to define the logger, the log_level here doesn't
        # really matter b/c we immediately disable all logging
        logger = cdislogging.get_logger("heal_cli", log_level="debug")
        # disables all logging
        logging.disable(logging.CRITICAL)


main.add_command(vlmd.vlmd)
if __name__ == "__main__":
    main()
