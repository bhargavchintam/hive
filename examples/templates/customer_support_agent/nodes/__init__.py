"""Node definitions for Customer Support Agent."""

from framework.graph import NodeSpec

# ---------------------------------------------------------------------------
# Node 1: Classify the incoming ticket
# ---------------------------------------------------------------------------
classify_ticket_node = NodeSpec(
    id="classify-ticket",
    name="Classify Ticket",
    description="Classify the support ticket by category, urgency, and sentiment",
    node_type="llm_generate",
    input_keys=["ticket_text", "customer_info"],
    output_keys=["category", "urgency", "sentiment", "tags"],
    system_prompt="""\
You are a support ticket classifier. Analyze the support request.

Ticket: {ticket_text}
Customer: {customer_info}

Classify the ticket across multiple dimensions:
- Category: technical, billing, feature_request, bug_report, general_inquiry
- Urgency: low, medium, high, critical
- Sentiment: positive, neutral, negative, frustrated
- Tags: Relevant keywords for routing and search

Output as JSON:
{{
  "category": "...",
  "urgency": "...",
  "sentiment": "...",
  "tags": ["tag1", "tag2"]
}}
""",
    tools=[],
    max_retries=2,
)

# ---------------------------------------------------------------------------
# Node 2: Search knowledge base for relevant articles
# ---------------------------------------------------------------------------
search_knowledge_base_node = NodeSpec(
    id="search-knowledge-base",
    name="Search Knowledge Base",
    description="Find relevant help articles and past solutions",
    node_type="event_loop",
    input_keys=["ticket_text", "category", "tags"],
    output_keys=["relevant_articles", "past_solutions"],
    system_prompt="""\
You are a knowledge base search specialist. Find relevant documentation.

Ticket: {ticket_text}
Category: {category}
Tags: {tags}

Available tools:
- web_search: Search for relevant articles and documentation
- grep_search: Search internal documentation

Steps:
1. Extract key search terms from the ticket
2. Search for relevant help articles
3. Search for similar past solutions
4. Return the most relevant matches

Output as JSON:
{{
  "relevant_articles": [
    {{"title": "...", "url": "...", "relevance": 0.95}}
  ],
  "past_solutions": [
    {{"ticket_id": "...", "solution": "...", "success_rate": 0.9}}
  ]
}}
""",
    tools=["web_search", "grep_search"],
    max_retries=2,
)

# ---------------------------------------------------------------------------
# Node 3: Generate initial response
# ---------------------------------------------------------------------------
generate_response_node = NodeSpec(
    id="generate-response",
    name="Generate Response",
    description="Generate a helpful, empathetic response to the customer",
    node_type="llm_generate",
    input_keys=["ticket_text", "customer_info", "relevant_articles", "category", "sentiment"],
    output_keys=["response_text", "response_tone", "suggested_actions"],
    system_prompt="""\
You are a customer support specialist. Generate a helpful response.

Ticket: {ticket_text}
Customer: {customer_info}
Category: {category}
Sentiment: {sentiment}
Relevant articles: {relevant_articles}

Guidelines:
- Match the customer's sentiment (empathetic if frustrated, professional if neutral)
- Provide clear, actionable steps
- Reference relevant documentation
- Set appropriate expectations

Output as JSON:
{{
  "response_text": "...",
  "response_tone": "empathetic | professional | friendly",
  "suggested_actions": [
    {{"action": "...", "reason": "..."}}
  ]
}}
""",
    tools=[],
    max_retries=2,
)

# ---------------------------------------------------------------------------
# Node 4: Quality check and escalation decision
# ---------------------------------------------------------------------------
quality_check_node = NodeSpec(
    id="quality-check",
    name="Quality Check",
    description="Review response quality and decide if escalation is needed",
    node_type="llm_generate",
    input_keys=["response_text", "ticket_text", "urgency", "category"],
    output_keys=["needs_escalation", "escalation_reason", "final_response", "quality_score"],
    system_prompt="""\
You are a quality assurance specialist. Review the support response.

Original ticket: {ticket_text}
Generated response: {response_text}
Urgency: {urgency}
Category: {category}

Check for:
- Response completeness and accuracy
- Appropriate tone and empathy
- Clear next steps
- Technical accuracy

Escalate if:
- Requires specialized knowledge
- High urgency with complex issue
- Customer is very frustrated
- Response doesn't fully address the issue

Output as JSON:
{{
  "needs_escalation": true/false,
  "escalation_reason": "..." or null,
  "final_response": "...",
  "quality_score": 0.0-1.0
}}
""",
    tools=[],
    max_retries=2,
)

# ---------------------------------------------------------------------------
# Node 5: Escalate to human agent
# ---------------------------------------------------------------------------
escalate_ticket_node = NodeSpec(
    id="escalate-ticket",
    name="Escalate Ticket",
    description="Prepare ticket for human agent escalation",
    node_type="llm_generate",
    input_keys=["ticket_text", "escalation_reason", "category", "relevant_articles"],
    output_keys=["escalation_summary", "recommended_agent", "priority_notes"],
    system_prompt="""\
You are an escalation coordinator. Prepare the ticket for human agent review.

Ticket: {ticket_text}
Escalation reason: {escalation_reason}
Category: {category}
Context: {relevant_articles}

Prepare handoff information:
- Concise summary of the issue
- Recommended specialist (technical, billing, product)
- Important context and customer history
- Suggested priority level

Output as JSON:
{{
  "escalation_summary": "...",
  "recommended_agent": "technical | billing | product",
  "priority_notes": "..."
}}
""",
    tools=[],
    max_retries=2,
)

# All nodes for easy import
all_nodes = [
    classify_ticket_node,
    search_knowledge_base_node,
    generate_response_node,
    quality_check_node,
    escalate_ticket_node,
]
