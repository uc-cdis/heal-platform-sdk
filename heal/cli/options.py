import click

from heal.vlmd.mappings.values import check_type_aliases


def parse_type_aliases(ctx, param, value):
    """Turn repeated '--map_type FROM TO' pairs into a {FROM: TO} dict"""
    if not value:
        return None
    type_aliases = dict(value)
    try:
        check_type_aliases(type_aliases)
    except ValueError as err:
        raise click.BadParameter(str(err))
    return type_aliases


map_type_option = click.option(
    "--map_type",
    "type_aliases",
    help=(
        "Treat FROM as the VLMD type TO in the 'type' column of a csv/tsv dictionary,"
        " e.g. --map_type 'Whole Number' integer. Can be repeated."
    ),
    nargs=2,
    multiple=True,
    metavar="FROM TO",
    callback=parse_type_aliases,
)
