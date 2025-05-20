import click
from cdislogging import get_logger

from heal.vlmd.extract.extract import vlmd_extract

logging = get_logger("__name__")


@click.command()
@click.option(
    "--input_file",
    "input_file",
    help="name of file to extract HEAL-compliant VLMD file",
    required=True,
    type=click.Path(writable=True),
)
@click.option(
    "--file_type",
    "file_type",
    help="Type of input file: auto, csv, json, tsv, dataset_csv, dataset_tsv, redcap",
    default="auto",
    type=str,
    show_default=True,
)
@click.option(
    "--title",
    "title",
    help="Root level title for the dictionary (required if extracting from csv to json)",
    default=None,
    type=str,
)
@click.option(
    "--output_dir",
    "output_dir",
    help="directory to write converted dictionary'",
    default=".",
    type=click.Path(writable=True),
    show_default=True,
)
def extract(input_file, title, file_type, output_dir):
    """Extract HEAL-compliant VLMD file from input file"""

    logging.info(f"Extracting VLMD from {input_file}")

    try:
        vlmd_extract(
            input_file,
            title=title,
            file_type=file_type,
            output_dir=output_dir,
        )
    except Exception as e:
        logging.error(f"Extraction error {str(e)}")
