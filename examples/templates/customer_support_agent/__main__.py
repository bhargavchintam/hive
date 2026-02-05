"""
CLI entry point for Customer Support Agent.

Uses AgentRuntime for automated ticket classification and response.
"""

import asyncio
import json
import logging
import sys
import click

from .agent import default_agent, CustomerSupportAgent


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
    """Customer Support Agent - Automated ticket classification and response."""
    pass


@cli.command()
@click.option("--ticket", "-t", type=str, required=True, help="Support ticket text")
@click.option("--customer-id", type=str, default="unknown", help="Customer ID")
@click.option("--customer-name", type=str, default="Customer", help="Customer name")
@click.option("--customer-email", type=str, default="customer@example.com", help="Customer email")
@click.option("--customer-tier", type=click.Choice(["free", "basic", "premium", "enterprise"]), default="basic", help="Customer tier")
@click.option("--mock", is_flag=True, help="Run in mock mode")
@click.option("--quiet", "-q", is_flag=True, help="Only output result JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--debug", is_flag=True, help="Show debug logging")
def respond(ticket, customer_id, customer_name, customer_email, customer_tier, mock, quiet, verbose, debug):
    """Generate automated response to a support ticket."""
    if not quiet:
        setup_logging(verbose=verbose, debug=debug)

    context = {
        "ticket_text": ticket,
        "customer_info": {
            "customer_id": customer_id,
            "name": customer_name,
            "email": customer_email,
            "tier": customer_tier,
        },
    }

    result = asyncio.run(default_agent.run(context, mock_mode=mock))

    output_data = {
        "category": result.get("category"),
        "urgency": result.get("urgency"),
        "sentiment": result.get("sentiment"),
        "response": result.get("final_response"),
        "needs_escalation": result.get("needs_escalation", False),
        "escalation_summary": result.get("escalation_summary"),
        "quality_score": result.get("quality_score"),
    }

    if not quiet:
        if output_data["needs_escalation"]:
            click.echo(f"\n⚠️  ESCALATION REQUIRED\n", err=True)
            click.echo(f"Reason: {output_data['escalation_summary']}\n", err=True)
        else:
            click.echo(f"\n✅ AUTOMATED RESPONSE READY\n", err=True)
            click.echo(f"Quality Score: {output_data['quality_score']:.2f}\n", err=True)

    click.echo(json.dumps(output_data, indent=2))


@cli.command()
@click.argument("input_json", type=click.File("r"))
@click.option("--mock", is_flag=True, help="Run in mock mode")
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--debug", is_flag=True, help="Show debug logging")
def batch(input_json, mock, verbose, debug):
    """Process support tickets from a JSON input file."""
    setup_logging(verbose=verbose, debug=debug)

    try:
        data = json.load(input_json)
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing input JSON: {e}", err=True)
        sys.exit(1)

    # Handle both single ticket and batch
    tickets = data if isinstance(data, list) else [data]
    results = []

    for ticket in tickets:
        result = asyncio.run(default_agent.run(ticket, mock_mode=mock))
        results.append({
            "ticket_id": ticket.get("ticket_id", "unknown"),
            "category": result.get("category"),
            "urgency": result.get("urgency"),
            "needs_escalation": result.get("needs_escalation", False),
            "response": result.get("final_response"),
        })

    click.echo(json.dumps(results, indent=2))


if __name__ == "__main__":
    cli()
