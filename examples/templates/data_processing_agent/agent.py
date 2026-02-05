"""Data Processing Agent — goal, edges, graph spec, and agent class."""

from pathlib import Path

from framework.graph import EdgeCondition, EdgeSpec, Goal, SuccessCriterion, Constraint
from framework.graph.edge import GraphSpec
from framework.graph.executor import GraphExecutor
from framework.runtime.core import Runtime
from framework.llm.anthropic import AnthropicProvider

from .config import default_config, RuntimeConfig
from .nodes import all_nodes

# ---------------------------------------------------------------------------
# Goal
# ---------------------------------------------------------------------------
goal = Goal(
    id="data-processing",
    name="Data Processing Pipeline",
    description=(
        "Load, transform, validate, and save data files with configurable "
        "transformation and quality rules."
    ),
    success_criteria=[
        SuccessCriterion(
            id="data-loaded",
            description="Data is successfully loaded with schema extracted",
            metric="output_contains",
            target="raw_data",
        ),
        SuccessCriterion(
            id="transformations-applied",
            description="All transformation rules are applied successfully",
            metric="output_contains",
            target="transformation_log",
        ),
        SuccessCriterion(
            id="validation-passed",
            description="Transformed data passes all quality checks",
            metric="custom",
            target="is_valid == True",
        ),
        SuccessCriterion(
            id="data-saved",
            description="Processed data is saved to output file",
            metric="output_contains",
            target="saved_path",
        ),
    ],
    constraints=[
        Constraint(
            id="no-data-loss",
            description="No rows should be lost unless explicitly filtered by rules",
            constraint_type="hard",
            category="quality",
        ),
        Constraint(
            id="preserve-schema",
            description="Output schema should match expected structure from rules",
            constraint_type="hard",
            category="quality",
        ),
        Constraint(
            id="processing-timeout",
            description="Processing should complete within 5 minutes",
            constraint_type="soft",
            category="performance",
        ),
    ],
    input_schema={
        "file_path": {"type": "string"},
        "file_type": {"type": "string", "enum": ["csv", "json"]},
        "transformation_rules": {"type": "array", "items": {"type": "object"}},
        "quality_rules": {"type": "array", "items": {"type": "object"}},
        "output_path": {"type": "string"},
        "output_format": {"type": "string", "enum": ["csv", "json"]},
    },
    output_schema={
        "final_data": {"type": "array"},
        "validation_report": {"type": "object"},
        "saved_path": {"type": "string"},
        "summary": {"type": "object"},
    },
)

# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------
edges = [
    EdgeSpec(
        id="load-to-transform",
        source="load-data",
        target="transform-data",
        condition=EdgeCondition.ON_SUCCESS,
        description="After loading data, proceed to transformation",
    ),
    EdgeSpec(
        id="transform-to-validate",
        source="transform-data",
        target="validate-output",
        condition=EdgeCondition.ON_SUCCESS,
        description="After transformation, validate the output",
    ),
    EdgeSpec(
        id="validate-to-transform-retry",
        source="validate-output",
        target="transform-data",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="is_valid == False",
        priority=10,
        description="If validation fails, retry transformation",
    ),
    EdgeSpec(
        id="validate-to-save",
        source="validate-output",
        target="save-data",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="is_valid == True",
        priority=5,
        description="If validation passes, save the data",
    ),
]

# ---------------------------------------------------------------------------
# Graph structure
# ---------------------------------------------------------------------------
graph = GraphSpec(
    nodes=all_nodes,
    edges=edges,
    entry_point="load-data",
    # Loop constraints
    max_iterations=50,
    max_tool_calls_per_turn=10,
    stall_detection_threshold=3,
)

# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class DataProcessingAgent:
    """
    Data Processing Agent with configurable transformation pipeline.

    This agent:
    1. Loads data from CSV or JSON files
    2. Applies transformation rules (cleaning, reshaping, filtering)
    3. Validates output against quality criteria
    4. Saves processed data to output format

    Features:
    - Handles CSV and JSON formats
    - Configurable transformation rules
    - Quality validation with detailed reporting
    - Automatic retry on validation failure
    """

    def __init__(self, config: RuntimeConfig = default_config):
        """Initialize the agent with runtime configuration."""
        self.config = config
        self.runtime = Runtime(
            graph=graph,
            goal=goal,
            llm_provider=AnthropicProvider(model=config.model),
            mock_mode=config.mock_mode,
            verbose=config.verbose,
        )

    async def run(self, context: dict) -> dict:
        """
        Execute the data processing pipeline.

        Args:
            context: Input context with keys:
                - file_path: Path to input data file
                - file_type: Type of file (csv, json)
                - transformation_rules: List of transformation rules to apply
                - quality_rules: List of quality checks to perform
                - output_path: Path for output file
                - output_format: Format for output (csv, json)

        Returns:
            Result dict with processed data and validation report
        """
        return await self.runtime.execute(context)


# Default agent instance
default_agent = DataProcessingAgent()
