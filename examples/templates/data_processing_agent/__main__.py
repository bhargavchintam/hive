"""
CLI entry point for Data Processing Agent.

Uses AgentRuntime for data transformation pipeline with validation.
"""

import asyncio
import json
import logging
import sys
import click

from .agent import default_agent, DataProcessingAgent


def setup_logging(verbose=False, debug=False):
    """Configure logging for execution visibility."""
    if debug:
        level, fmt = logging.DEBUG, "%(asctime)s %(name)s: %(message)s"
    elif verbose:
        level, fmt = logging.INFO, "%(message)s"
    else:
        level, fmt = logging.WARNING, "%(levelname)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, stream=sys.stderr)
    logging.getLogger("framework").setLevel(level)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Data Processing Agent - ETL pipeline with validation."""
    pass


@cli.command()
@click.option("--file-path", "-f", type=str, required=True, help="Input data file path")
@click.option("--file-type", "-t", type=click.Choice(["csv", "json"]), default="csv", help="Input file type")
@click.option("--output-path", "-o", type=str, required=True, help="Output file path")
@click.option("--output-format", type=click.Choice(["csv", "json"]), default="csv", help="Output format")
@click.option("--rules", "-r", type=str, help="JSON string with transformation and quality rules")
@click.option("--mock", is_flag=True, help="Run in mock mode")
@click.option("--quiet", "-q", is_flag=True, help="Only output result JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--debug", is_flag=True, help="Show debug logging")
def process(file_path, file_type, output_path, output_format, rules, mock, quiet, verbose, debug):
    """Process data file with transformation and validation pipeline."""
    if not quiet:
        setup_logging(verbose=verbose, debug=debug)

    # Parse rules if provided
    transformation_rules = []
    quality_rules = []

    if rules:
        try:
            parsed_rules = json.loads(rules)
            transformation_rules = parsed_rules.get("transformations", [])
            quality_rules = parsed_rules.get("quality_checks", [])
        except json.JSONDecodeError as e:
            click.echo(f"Error parsing rules JSON: {e}", err=True)
            sys.exit(1)

    context = {
        "file_path": file_path,
        "file_type": file_type,
        "transformation_rules": transformation_rules,
        "quality_rules": quality_rules,
        "output_path": output_path,
        "output_format": output_format,
    }

    result = asyncio.run(default_agent.run(context, mock_mode=mock))

    output_data = {
        "status": "success" if result.get("is_valid") else "failed",
        "validation_report": result.get("validation_report"),
        "saved_path": result.get("saved_path"),
        "summary": result.get("summary"),
    }

    click.echo(json.dumps(output_data, indent=2))


@cli.command()
@click.argument("input_json", type=click.File("r"))
@click.option("--mock", is_flag=True, help="Run in mock mode")
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--debug", is_flag=True, help="Show debug logging")
def batch(input_json, mock, verbose, debug):
    """Process data from a JSON input file with full configuration."""
    setup_logging(verbose=verbose, debug=debug)

    try:
        context = json.load(input_json)
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing input JSON: {e}", err=True)
        sys.exit(1)

    result = asyncio.run(default_agent.run(context, mock_mode=mock))
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    cli()
