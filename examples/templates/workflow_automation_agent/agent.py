"""Workflow Automation Agent — goal, edges, graph spec, and agent class."""

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
    id="workflow-automation",
    name="Workflow Automation Orchestrator",
    description=(
        "Execute multi-step workflows with conditional branching, parallel execution, "
        "and error handling."
    ),
    success_criteria=[
        SuccessCriterion(
            id="workflow-parsed",
            description="Workflow definition is parsed and validated",
            metric="output_contains",
            target="execution_plan",
        ),
        SuccessCriterion(
            id="steps-executed",
            description="All required workflow steps are executed",
            metric="custom",
            target="success_count > 0",
        ),
        SuccessCriterion(
            id="results-aggregated",
            description="Results from all steps are collected and combined",
            metric="output_contains",
            target="final_results",
        ),
        SuccessCriterion(
            id="errors-handled",
            description="Errors are handled gracefully with retry or fallback",
            metric="custom",
            target="failed_count == 0 or error_resolved == True",
        ),
    ],
    constraints=[
        Constraint(
            id="step-dependencies",
            description="Steps must execute in dependency order",
            constraint_type="hard",
            category="correctness",
        ),
        Constraint(
            id="no-infinite-loops",
            description="Conditional branches must not create infinite loops",
            constraint_type="hard",
            category="safety",
        ),
        Constraint(
            id="timeout-limit",
            description="Workflow must complete within timeout",
            constraint_type="soft",
            category="performance",
        ),
    ],
    input_schema={
        "workflow_definition": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "steps": {"type": "array"},
                "conditions": {"type": "object"},
                "retry_policy": {"type": "object"},
            },
        },
        "input_data": {"type": "object"},
    },
    output_schema={
        "final_results": {"type": "object"},
        "execution_summary": {"type": "object"},
        "success_count": {"type": "integer"},
        "failed_count": {"type": "integer"},
    },
)

# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------
edges = [
    EdgeSpec(
        id="parse-to-execute",
        source="parse-workflow",
        target="execute-step",
        condition=EdgeCondition.ON_SUCCESS,
        description="After parsing workflow, execute first step",
    ),
    EdgeSpec(
        id="execute-to-evaluate",
        source="execute-step",
        target="evaluate-conditions",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="step_status == 'success' and has_conditions == True",
        priority=10,
        description="If step succeeded and has conditions, evaluate them",
    ),
    EdgeSpec(
        id="execute-to-next-step",
        source="execute-step",
        target="execute-step",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="step_status == 'success' and has_next_step == True",
        priority=5,
        description="If step succeeded and more steps exist, execute next",
    ),
    EdgeSpec(
        id="execute-to-error",
        source="execute-step",
        target="error-handler",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="step_status == 'failed'",
        priority=15,
        description="If step failed, handle error",
    ),
    EdgeSpec(
        id="evaluate-to-execute",
        source="evaluate-conditions",
        target="execute-step",
        condition=EdgeCondition.ON_SUCCESS,
        description="After evaluating conditions, execute next steps",
    ),
    EdgeSpec(
        id="error-to-retry",
        source="error-handler",
        target="execute-step",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="should_retry == True",
        priority=10,
        description="If should retry, re-execute step",
    ),
    EdgeSpec(
        id="error-to-aggregate",
        source="error-handler",
        target="aggregate-results",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="should_retry == False",
        priority=5,
        description="If no retry, proceed to aggregate results",
    ),
    EdgeSpec(
        id="execute-to-aggregate",
        source="execute-step",
        target="aggregate-results",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="all_steps_complete == True",
        priority=1,
        description="When all steps complete, aggregate results",
    ),
]

# ---------------------------------------------------------------------------
# Graph structure
# ---------------------------------------------------------------------------
graph = GraphSpec(
    nodes=all_nodes,
    edges=edges,
    entry_point="parse-workflow",
    # Loop constraints
    max_iterations=100,
    max_tool_calls_per_turn=15,
    stall_detection_threshold=3,
)

# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class WorkflowAutomationAgent:
    """
    Workflow Automation Agent for orchestrating multi-step processes.

    This agent:
    1. Parses workflow definitions with steps and dependencies
    2. Executes steps in proper order
    3. Evaluates conditional branches
    4. Handles errors with retry logic
    5. Aggregates results from all steps

    Features:
    - Dependency-aware execution
    - Conditional branching
    - Parallel step execution
    - Automatic error handling and retry
    - Comprehensive result aggregation
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
        Execute a workflow automation task.

        Args:
            context: Input context with keys:
                - workflow_definition: The workflow structure with steps
                - input_data: Initial data for the workflow

        Returns:
            Result dict with aggregated outputs and execution summary
        """
        return await self.runtime.execute(context)


# Default agent instance
default_agent = WorkflowAutomationAgent()
