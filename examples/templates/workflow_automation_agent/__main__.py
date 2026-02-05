"""
CLI entry point for Workflow Automation Agent.

Uses AgentRuntime for multi-step workflow orchestration.
"""

import asyncio
import json
import logging
import sys
import click

from .agent import default_agent, WorkflowAutomationAgent


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
    """Workflow Automation Agent - Multi-step workflow orchestration."""
    pass


@cli.command()
@click.argument("workflow_file", type=click.File("r"))
@click.option("--input-data", "-i", type=str, help="JSON string with input data")
@click.option("--mock", is_flag=True, help="Run in mock mode")
@click.option("--quiet", "-q", is_flag=True, help="Only output result JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show execution details")
@click.option("--debug", is_flag=True, help="Show debug logging")
def execute(workflow_file, input_data, mock, quiet, verbose, debug):
    """Execute a workflow from a definition file."""
    if not quiet:
        setup_logging(verbose=verbose, debug=debug)

    try:
        workflow_definition = json.load(workflow_file)
    except json.JSONDecodeError as e:
        click.echo(f"Error parsing workflow JSON: {e}", err=True)
        sys.exit(1)

    # Parse input data if provided
    parsed_input_data = {}
    if input_data:
        try:
            parsed_input_data = json.loads(input_data)
        except json.JSONDecodeError as e:
            click.echo(f"Error parsing input data JSON: {e}", err=True)
            sys.exit(1)

    context = {
        "workflow_definition": workflow_definition,
        "input_data": parsed_input_data,
    }

    result = asyncio.run(default_agent.run(context, mock_mode=mock))

    output_data = {
        "final_results": result.get("final_results"),
        "execution_summary": result.get("execution_summary"),
        "success_count": result.get("success_count", 0),
        "failed_count": result.get("failed_count", 0),
    }

    if not quiet:
        if output_data["failed_count"] > 0:
            click.echo(f"\n⚠️  WORKFLOW COMPLETED WITH ERRORS\n", err=True)
            click.echo(f"Success: {output_data['success_count']}, Failed: {output_data['failed_count']}\n", err=True)
        else:
            click.echo(f"\n✅ WORKFLOW COMPLETED SUCCESSFULLY\n", err=True)
            click.echo(f"Steps executed: {output_data['success_count']}\n", err=True)

    click.echo(json.dumps(output_data, indent=2))


@cli.command()
@click.option("--name", "-n", type=str, required=True, help="Workflow name")
@click.option("--steps", "-s", type=int, default=3, help="Number of steps")
def template(name, steps):
    """Generate a workflow template file."""
    workflow = {
        "name": name,
        "steps": [
            {
                "step_id": f"step_{i+1}",
                "type": "api_call" if i == 0 else "data_transform",
                "action": f"Action for step {i+1}",
                "inputs": ["input_data"] if i == 0 else [f"step_{i}_output"],
                "outputs": [f"step_{i+1}_output"],
                "description": f"Description for step {i+1}",
            }
            for i in range(steps)
        ],
        "conditions": {
            "example_condition": {
                "if": "step_1_output.status == 'success'",
                "then": "step_2",
                "else": "error_handler",
            }
        },
        "retry_policy": {
            "max_retries": 3,
            "retry_delay_seconds": 5,
            "retry_on": ["network_error", "timeout"],
        },
    }

    filename = f"{name.lower().replace(' ', '_')}_workflow.json"
    with open(filename, "w") as f:
        json.dump(workflow, f, indent=2)

    click.echo(f"✅ Workflow template created: {filename}")


@cli.command()
@click.argument("workflow_file", type=click.File("r"))
def validate(workflow_file):
    """Validate a workflow definition."""
    try:
        workflow = json.load(workflow_file)
    except json.JSONDecodeError as e:
        click.echo(f"❌ Invalid JSON: {e}", err=True)
        sys.exit(1)

    # Basic validation
    errors = []

    if "name" not in workflow:
        errors.append("Missing required field: name")

    if "steps" not in workflow or not isinstance(workflow["steps"], list):
        errors.append("Missing or invalid field: steps")
    else:
        step_ids = set()
        for i, step in enumerate(workflow["steps"]):
            if "step_id" not in step:
                errors.append(f"Step {i}: missing step_id")
            else:
                if step["step_id"] in step_ids:
                    errors.append(f"Duplicate step_id: {step['step_id']}")
                step_ids.add(step["step_id"])

            if "type" not in step:
                errors.append(f"Step {step.get('step_id', i)}: missing type")

            if "inputs" not in step or not isinstance(step["inputs"], list):
                errors.append(f"Step {step.get('step_id', i)}: missing or invalid inputs")

            if "outputs" not in step or not isinstance(step["outputs"], list):
                errors.append(f"Step {step.get('step_id', i)}: missing or invalid outputs")

    if errors:
        click.echo(f"❌ Validation failed:\n")
        for error in errors:
            click.echo(f"  - {error}")
        sys.exit(1)
    else:
        click.echo(f"✅ Workflow validation passed")


if __name__ == "__main__":
    cli()
