import click
from cdislogging import get_logger
from jsonschema import ValidationError

from heal.vlmd.validate.validate import vlmd_validate

logging = get_logger("__name__")


@click.command()
@click.option(
    "--input_file",
    "input_file",
    required=True,
    help="name of file to validate",
    type=click.Path(writable=True),
)
def validate(input_file):
    """Validate VLMD input file"""

    logging.info(f"Validating VLMD file{input_file}")

    try:
        vlmd_validate(input_file)
        logging.info("Valid")
    except ValidationError as err:
        logging.error(f"Error in validating dictionary from {input_file}")
        logging.error(err.message)
    except Exception as e:
        logging.error(f"Validation error {str(e)}")
        logging.error("Invalid file")
