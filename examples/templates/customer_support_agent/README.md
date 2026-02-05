# Customer Support Agent

A Hive agent that automates customer support ticket classification, knowledge base search, response generation, and intelligent escalation to human agents.

## What This Template Demonstrates

- **Ticket classification**: Automatic categorization by type, urgency, and sentiment
- **Knowledge base integration**: Search for relevant articles and past solutions
- **Response generation**: Empathetic, helpful responses tailored to customer sentiment
- **Quality assurance**: Automatic response quality checking with retry logic
- **Intelligent escalation**: Route complex cases to appropriate human specialists

## Agent Architecture

```
┌──────────────────┐
│ classify-ticket  │  (LLMNode: Category, urgency, sentiment analysis)
└────────┬─────────┘
         │ ON_SUCCESS
         v
┌────────────────────────┐
│ search-knowledge-base  │  (EventLoopNode: Find relevant articles/solutions)
└────────┬───────────────┘
         │ ON_SUCCESS
         v
┌──────────────────────┐
│  generate-response   │  (LLMNode: Create customer response)
└────────┬─────────────┘
         │ ON_SUCCESS
         v
┌──────────────────┐
│  quality-check   │  (LLMNode: Review and decide escalation)
└────┬─────────┬───┘
     │         │
     │         └─ CONDITIONAL (quality_score < 0.7) ─┐
     │                                               │
     │ CONDITIONAL (needs_escalation == True)       v
     v                                      (Back to generate)
┌──────────────────┐
│ escalate-ticket  │  (LLMNode: Prepare for human agent)
└──────────────────┘
```

## Usage

### Single Ticket Response

```bash
# Basic ticket processing
uv run python -m examples.templates.customer_support_agent respond \
  --ticket "My password reset email never arrived" \
  --customer-name "John Doe" \
  --customer-email "john@example.com"

# Premium customer with detailed context
uv run python -m examples.templates.customer_support_agent respond \
  --ticket "The API is returning 500 errors for all requests since this morning" \
  --customer-tier enterprise \
  --customer-name "Jane Smith" \
  --customer-email "jane@techcorp.com"
```

### Batch Processing

```bash
# Process multiple tickets from JSON file
uv run python -m examples.templates.customer_support_agent batch tickets.json
```

Example `tickets.json`:
```json
[
  {
    "ticket_id": "TICKET-001",
    "ticket_text": "I can't log in to my account",
    "customer_info": {
      "customer_id": "cust_123",
      "name": "Alice Johnson",
      "email": "alice@example.com",
      "tier": "basic"
    }
  },
  {
    "ticket_id": "TICKET-002",
    "ticket_text": "Billing charged me twice this month",
    "customer_info": {
      "customer_id": "cust_456",
      "name": "Bob Williams",
      "email": "bob@example.com",
      "tier": "premium"
    }
  }
]
```

## Output Example

```json
{
  "category": "technical",
  "urgency": "medium",
  "sentiment": "frustrated",
  "response": "Hi John,\n\nI understand how frustrating it can be when you don't receive important emails. Let me help you with that.\n\nFirst, please check your spam/junk folder...",
  "needs_escalation": false,
  "escalation_summary": null,
  "quality_score": 0.89
}
```

## Ticket Classification

### Categories
- `technical` - Technical issues, bugs, errors
- `billing` - Payment, subscription, invoicing
- `feature_request` - New feature suggestions
- `bug_report` - Reported software bugs
- `general_inquiry` - General questions

### Urgency Levels
- `low` - Can wait, not time-sensitive
- `medium` - Should be addressed soon
- `high` - Important, affects customer work
- `critical` - Service down, blocking work

### Sentiment Analysis
- `positive` - Happy, satisfied customer
- `neutral` - Factual, no strong emotion
- `negative` - Unhappy, disappointed
- `frustrated` - Angry, multiple issues

## Escalation Criteria

The agent automatically escalates when:
- **High complexity**: Requires specialized technical knowledge
- **Critical urgency**: Service outage or data loss
- **Frustrated customer**: Multiple negative interactions
- **Low confidence**: Quality score < 0.7 after retries
- **Policy decisions**: Requires manager approval

## Customization

### Adding Categories

Edit `nodes/__init__.py` → `classify_ticket_node` → `system_prompt`:
```python
# Add new categories to the list
- Category: technical, billing, feature_request, bug_report, custom_category
```

### Changing Escalation Rules

Edit `nodes/__init__.py` → `quality_check_node` → `system_prompt`:
```python
Escalate if:
- Requires specialized knowledge
- High urgency with complex issue
- Customer is very frustrated
- Your custom rule here
```

### Knowledge Base Integration

Edit `nodes/__init__.py` → `search_knowledge_base_node`:
- Add custom search tools
- Connect to internal documentation systems
- Search CRM for customer history

## Input Schema

```json
{
  "ticket_text": "string (required)",
  "customer_info": {
    "customer_id": "string (required)",
    "name": "string (required)",
    "email": "string (required)",
    "tier": "free | basic | premium | enterprise"
  }
}
```

## Output Schema

```json
{
  "category": "string",
  "urgency": "string",
  "sentiment": "string",
  "final_response": "string",
  "needs_escalation": "boolean",
  "escalation_summary": "string | null",
  "quality_score": "number (0-1)"
}
```

## Response Quality Metrics

The quality check evaluates:
1. **Completeness**: Does it address all customer concerns?
2. **Accuracy**: Is the information technically correct?
3. **Tone**: Is it empathetic and appropriate for sentiment?
4. **Actionability**: Does it provide clear next steps?
5. **Professionalism**: Is it well-written and error-free?

Score interpretation:
- `0.9-1.0` - Excellent response, ready to send
- `0.7-0.9` - Good response, acceptable
- `0.5-0.7` - Needs improvement, regenerate
- `< 0.5` - Poor response, likely escalate

## Example Use Cases

1. **First-line support automation**: Handle common tickets automatically
2. **After-hours support**: Provide instant responses outside business hours
3. **Ticket routing**: Classify and route to appropriate team
4. **Quality assurance**: Ensure consistent response quality
5. **Customer sentiment tracking**: Monitor customer satisfaction trends

## Integration Points

- **CRM systems**: Pull customer history, update ticket status
- **Knowledge bases**: Search Confluence, Notion, internal docs
- **Email**: Send responses via email integration
- **Slack/Teams**: Post escalations to support channels
- **Analytics**: Track response quality, escalation rates, CSAT

## Extending This Template

- **Multi-language support**: Add translation for global customers
- **Attachment handling**: Process screenshots, log files
- **Live chat integration**: Connect to chat platforms
- **SLA tracking**: Monitor response time against SLAs
- **Feedback loop**: Learn from human agent corrections

## Best Practices

1. **Always empathize**: Match customer sentiment with appropriate tone
2. **Set expectations**: Be clear about timelines and next steps
3. **Link to docs**: Reference help articles for self-service
4. **Escalate wisely**: Don't let frustrated customers wait
5. **Track metrics**: Monitor quality scores and escalation rates
