# Workflow Automation Agent

A Hive agent that orchestrates complex multi-step workflows with conditional branching, dependency management, parallel execution, error handling, and result aggregation.

## What This Template Demonstrates

- **Multi-step orchestration**: Execute workflows with multiple dependent steps
- **Conditional branching**: Dynamic routing based on step results
- **Error handling**: Automatic retry logic with fallback strategies
- **Dependency management**: Ensure steps execute in correct order
- **Result aggregation**: Collect and combine outputs from all steps

## Agent Architecture

```
┌──────────────────┐
│  parse-workflow  │  (LLMNode: Parse definition, create execution plan)
└────────┬─────────┘
         │ ON_SUCCESS
         v
┌──────────────────┐
│  execute-step    │  (EventLoopNode: Execute workflow step with tools)
└───┬──────┬───────┘
    │      │
    │      └─ CONDITIONAL (step_status == 'failed') ──────┐
    │                                                       v
    │                                              ┌────────────────┐
    │                                              │ error-handler  │
    │                                              └────┬───────┬───┘
    │                                                   │       │
    │                                                   │       └─ (should_retry == False)
    │                                                   │                 │
    │ CONDITIONAL (has_conditions)                      │                 v
    v                                                   │         ┌──────────────────┐
┌───────────────────────┐                              │         │ aggregate-results│
│ evaluate-conditions   │                              │         └──────────────────┘
└────────┬──────────────┘                              │
         │                                              │
         └─ ON_SUCCESS ─────────────────────────────────┘
                                                        │
                                                        └─ (should_retry == True)
                                                                  │
                                                                  v
                                                        (Back to execute-step)
```

## Usage

### Execute a Workflow

```bash
# Execute workflow from definition file
uv run python -m examples.templates.workflow_automation_agent execute workflow.json

# With input data
uv run python -m examples.templates.workflow_automation_agent execute workflow.json \
  --input-data '{"customer_id": "123", "order_id": "456"}'

# With verbose output
uv run python -m examples.templates.workflow_automation_agent execute workflow.json \
  --verbose
```

### Generate a Workflow Template

```bash
# Create a basic workflow template
uv run python -m examples.templates.workflow_automation_agent template \
  --name "Order Processing" \
  --steps 5

# Creates: order_processing_workflow.json
```

### Validate a Workflow

```bash
# Validate workflow definition
uv run python -m examples.templates.workflow_automation_agent validate workflow.json
```

## Workflow Definition Format

```json
{
  "name": "Customer Onboarding Workflow",
  "steps": [
    {
      "step_id": "create_account",
      "type": "api_call",
      "action": "Create customer account in CRM",
      "inputs": ["customer_data"],
      "outputs": ["account_id", "account_status"],
      "description": "Create new customer account"
    },
    {
      "step_id": "send_welcome_email",
      "type": "notification",
      "action": "Send welcome email to customer",
      "inputs": ["account_id", "customer_email"],
      "outputs": ["email_sent"],
      "description": "Send onboarding email"
    },
    {
      "step_id": "setup_trial",
      "type": "api_call",
      "action": "Activate trial subscription",
      "inputs": ["account_id"],
      "outputs": ["trial_activated", "trial_end_date"],
      "description": "Enable trial period"
    }
  ],
  "conditions": {
    "premium_customer": {
      "if": "customer_data.tier == 'premium'",
      "then": "assign_account_manager",
      "else": "send_self_service_guide"
    }
  },
  "retry_policy": {
    "max_retries": 3,
    "retry_delay_seconds": 5,
    "retry_on": ["network_error", "timeout", "rate_limit"]
  }
}
```

## Step Types

### API Call
Execute HTTP requests or API calls:
```json
{
  "step_id": "fetch_user_data",
  "type": "api_call",
  "action": "GET /api/users/{user_id}",
  "inputs": ["user_id"],
  "outputs": ["user_profile"]
}
```

### Data Transform
Transform data structures:
```json
{
  "step_id": "format_data",
  "type": "data_transform",
  "action": "Convert CSV to JSON",
  "inputs": ["raw_csv"],
  "outputs": ["formatted_json"]
}
```

### File Operation
File system operations:
```json
{
  "step_id": "save_report",
  "type": "file_operation",
  "action": "Write report to file",
  "inputs": ["report_content"],
  "outputs": ["file_path"]
}
```

### Notification
Send emails or messages:
```json
{
  "step_id": "alert_team",
  "type": "notification",
  "action": "Send Slack notification",
  "inputs": ["message", "channel"],
  "outputs": ["notification_sent"]
}
```

### Condition Check
Evaluate conditions:
```json
{
  "step_id": "check_threshold",
  "type": "condition_check",
  "action": "Check if value exceeds threshold",
  "inputs": ["value", "threshold"],
  "outputs": ["exceeds_threshold"]
}
```

## Conditional Branching

Define conditions that determine workflow paths:

```json
{
  "conditions": {
    "high_priority": {
      "if": "ticket.urgency == 'critical'",
      "then": "escalate_to_manager",
      "else": "assign_to_queue"
    },
    "payment_successful": {
      "if": "payment_status.success == true",
      "then": "send_receipt",
      "else": "retry_payment"
    }
  }
}
```

## Error Handling

Configure retry policies and fallback strategies:

```json
{
  "retry_policy": {
    "max_retries": 3,
    "retry_delay_seconds": 5,
    "retry_on": ["network_error", "timeout"],
    "backoff_strategy": "exponential"
  },
  "fallback_actions": {
    "create_account_failed": "use_default_account",
    "email_send_failed": "log_and_continue"
  }
}
```

## Output Example

```json
{
  "final_results": {
    "create_account": {
      "account_id": "acc_789",
      "account_status": "active"
    },
    "send_welcome_email": {
      "email_sent": true
    },
    "setup_trial": {
      "trial_activated": true,
      "trial_end_date": "2024-03-01"
    }
  },
  "execution_summary": {
    "total_steps": 3,
    "executed": 3,
    "skipped": 0,
    "duration_seconds": 12.5
  },
  "success_count": 3,
  "failed_count": 0
}
```

## Example Workflows

### 1. Data Pipeline

```json
{
  "name": "Daily Sales Report",
  "steps": [
    {"step_id": "extract", "type": "api_call", "action": "Fetch sales data"},
    {"step_id": "transform", "type": "data_transform", "action": "Aggregate by region"},
    {"step_id": "load", "type": "file_operation", "action": "Save to CSV"},
    {"step_id": "notify", "type": "notification", "action": "Email report to team"}
  ]
}
```

### 2. Customer Support Escalation

```json
{
  "name": "Ticket Escalation Workflow",
  "steps": [
    {"step_id": "classify", "type": "data_transform", "action": "Classify ticket"},
    {"step_id": "check_urgency", "type": "condition_check", "action": "Check priority"},
    {"step_id": "assign", "type": "api_call", "action": "Assign to agent"}
  ],
  "conditions": {
    "urgent_ticket": {
      "if": "urgency == 'critical'",
      "then": "escalate_to_manager",
      "else": "assign_to_queue"
    }
  }
}
```

### 3. Deployment Pipeline

```json
{
  "name": "CI/CD Deployment",
  "steps": [
    {"step_id": "run_tests", "type": "api_call", "action": "Execute test suite"},
    {"step_id": "build", "type": "api_call", "action": "Build application"},
    {"step_id": "deploy_staging", "type": "api_call", "action": "Deploy to staging"},
    {"step_id": "smoke_tests", "type": "api_call", "action": "Run smoke tests"},
    {"step_id": "deploy_prod", "type": "api_call", "action": "Deploy to production"}
  ],
  "conditions": {
    "tests_pass": {
      "if": "smoke_tests.success == true",
      "then": "deploy_prod",
      "else": "rollback_staging"
    }
  },
  "retry_policy": {
    "max_retries": 2,
    "retry_on": ["deployment_timeout"]
  }
}
```

## Customization

### Adding New Step Types

Edit `nodes/__init__.py` → `execute_step_node` → add new step type handling:

```python
# Add support for database operations
- database_query: Execute SQL queries
```

### Modifying Retry Logic

Edit `nodes/__init__.py` → `error_handler_node` → customize retry strategy:

```python
# Add exponential backoff
# Add custom error classification
# Configure per-step retry policies
```

### Parallel Execution

Edit `agent.py` → `edges` to support parallel step execution:

```python
# Allow multiple steps to run concurrently
# Synchronize at merge points
```

## Input Schema

```json
{
  "workflow_definition": {
    "name": "string (required)",
    "steps": "array (required)",
    "conditions": "object (optional)",
    "retry_policy": "object (optional)"
  },
  "input_data": "object (optional)"
}
```

## Output Schema

```json
{
  "final_results": "object",
  "execution_summary": {
    "total_steps": "integer",
    "executed": "integer",
    "skipped": "integer",
    "duration_seconds": "number"
  },
  "success_count": "integer",
  "failed_count": "integer"
}
```

## Use Cases

1. **ETL Pipelines**: Extract, transform, load data workflows
2. **CI/CD Automation**: Build, test, deploy sequences
3. **Business Process Automation**: Order processing, onboarding, approvals
4. **Data Quality Checks**: Multi-stage validation pipelines
5. **Integration Workflows**: Connect multiple systems and services
6. **Scheduled Jobs**: Nightly reports, backups, cleanups
7. **Event-Driven Workflows**: React to webhooks, triggers

## Best Practices

1. **Define clear dependencies**: Ensure inputs/outputs match between steps
2. **Use descriptive step IDs**: Make workflows self-documenting
3. **Handle errors gracefully**: Configure appropriate retry policies
4. **Validate workflows**: Use the validate command before execution
5. **Monitor execution**: Enable verbose logging for debugging
6. **Test conditions**: Verify conditional logic with mock data
7. **Version workflows**: Track changes to workflow definitions

## Extending This Template

- **Add persistence**: Save workflow state for resume after failures
- **Implement scheduling**: Trigger workflows at specific times
- **Add webhooks**: Start workflows from external events
- **Enable parallelism**: Execute independent steps concurrently
- **Add monitoring**: Track metrics, logs, and alerts
- **Build UI**: Create visual workflow designer

## Performance Considerations

- **Parallel execution**: Independent steps can run in parallel
- **Caching**: Cache repeated API calls or computations
- **Timeout management**: Set appropriate timeouts for long-running steps
- **Resource limits**: Control memory and CPU usage
- **Batch processing**: Group similar operations for efficiency

## Troubleshooting

### Workflow Fails at Step X
- Check step inputs are available from previous steps
- Verify required tools/credentials are configured
- Review error logs for specific failure reason

### Infinite Loop Detected
- Check conditional logic doesn't create cycles
- Ensure retry policies have max_retries limits
- Review step dependencies for circular references

### Slow Execution
- Identify long-running steps in execution summary
- Consider parallel execution for independent steps
- Add timeout limits to prevent hanging

## Integration Points

- **APIs**: REST, GraphQL, SOAP endpoints
- **Databases**: SQL queries, NoSQL operations
- **File systems**: Read/write files, process documents
- **Email/Messaging**: SMTP, Slack, Teams notifications
- **Cloud services**: AWS, GCP, Azure integrations
- **Monitoring**: Datadog, New Relic, Prometheus metrics
