"""Customer Support Agent — goal, edges, graph spec, and agent class."""

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
    id="customer-support",
    name="Customer Support Automation",
    description=(
        "Classify, research, and respond to customer support tickets with "
        "automatic escalation for complex cases."
    ),
    success_criteria=[
        SuccessCriterion(
            id="ticket-classified",
            description="Ticket is properly classified with category, urgency, and sentiment",
            metric="output_contains",
            target="category",
        ),
        SuccessCriterion(
            id="knowledge-searched",
            description="Relevant knowledge base articles are found",
            metric="output_contains",
            target="relevant_articles",
        ),
        SuccessCriterion(
            id="response-generated",
            description="A helpful response is generated for the customer",
            metric="output_contains",
            target="final_response",
        ),
        SuccessCriterion(
            id="quality-checked",
            description="Response passes quality review or is escalated",
            metric="custom",
            target="quality_score > 0.7 or needs_escalation == True",
        ),
    ],
    constraints=[
        Constraint(
            id="empathetic-tone",
            description="Responses must be empathetic and professional",
            constraint_type="hard",
            category="quality",
        ),
        Constraint(
            id="no-promises",
            description="Don't promise specific timelines or features without confirmation",
            constraint_type="hard",
            category="safety",
        ),
        Constraint(
            id="response-time",
            description="Automated response should be generated within 30 seconds",
            constraint_type="soft",
            category="performance",
        ),
    ],
    input_schema={
        "ticket_text": {"type": "string"},
        "customer_info": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "name": {"type": "string"},
                "email": {"type": "string"},
                "tier": {"type": "string", "enum": ["free", "basic", "premium", "enterprise"]},
            },
        },
    },
    output_schema={
        "category": {"type": "string"},
        "urgency": {"type": "string"},
        "final_response": {"type": "string"},
        "needs_escalation": {"type": "boolean"},
        "escalation_summary": {"type": "string", "nullable": True},
    },
)

# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------
edges = [
    EdgeSpec(
        id="classify-to-search",
        source="classify-ticket",
        target="search-knowledge-base",
        condition=EdgeCondition.ON_SUCCESS,
        description="After classification, search for relevant information",
    ),
    EdgeSpec(
        id="search-to-generate",
        source="search-knowledge-base",
        target="generate-response",
        condition=EdgeCondition.ON_SUCCESS,
        description="After finding knowledge, generate response",
    ),
    EdgeSpec(
        id="generate-to-quality",
        source="generate-response",
        target="quality-check",
        condition=EdgeCondition.ON_SUCCESS,
        description="After generating response, check quality",
    ),
    EdgeSpec(
        id="quality-to-escalate",
        source="quality-check",
        target="escalate-ticket",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="needs_escalation == True",
        priority=10,
        description="If escalation needed, prepare handoff to human agent",
    ),
    EdgeSpec(
        id="quality-to-regenerate",
        source="quality-check",
        target="generate-response",
        condition=EdgeCondition.CONDITIONAL,
        condition_expr="quality_score < 0.7 and needs_escalation == False",
        priority=5,
        description="If quality is low but doesn't need escalation, regenerate",
    ),
]

# ---------------------------------------------------------------------------
# Graph structure
# ---------------------------------------------------------------------------
graph = GraphSpec(
    nodes=all_nodes,
    edges=edges,
    entry_point="classify-ticket",
    # Loop constraints
    max_iterations=50,
    max_tool_calls_per_turn=10,
    stall_detection_threshold=3,
)

# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class CustomerSupportAgent:
    """
    Customer Support Agent with automatic classification and escalation.

    This agent:
    1. Classifies incoming support tickets
    2. Searches knowledge base for relevant information
    3. Generates empathetic, helpful responses
    4. Quality checks responses
    5. Escalates complex cases to human agents

    Features:
    - Automatic ticket classification (category, urgency, sentiment)
    - Knowledge base integration
    - Empathetic response generation
    - Quality assurance with automatic retry
    - Intelligent escalation to human agents
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
        Process a customer support ticket.

        Args:
            context: Input context with keys:
                - ticket_text: The customer's support request
                - customer_info: Object with customer_id, name, email, tier

        Returns:
            Result dict with response and escalation information
        """
        return await self.runtime.execute(context)


# Default agent instance
default_agent = CustomerSupportAgent()
