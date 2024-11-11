import click

from cdislogging import get_logger

from heal.vlmd.validate.validate import vlmd_validate

logging = get_logger("__name__")


@click.command()
@click.option(
    "--input_file",
    "input_file",
    help="name of file to validate",
    type=click.Path(writable=True),
)
def validate(input_file):
    """Validate VLMD input file"""

    logging.info(f"Validating VLMD file{input_file}")

    try:
        vlmd_validate(input_file)
    except Exception as e:
        logging.warning(str(e))
        raise e
    logging.info("Valid")
