"""Node definitions for Workflow Automation Agent."""

from framework.graph import NodeSpec

# ---------------------------------------------------------------------------
# Node 1: Parse workflow definition
# ---------------------------------------------------------------------------
parse_workflow_node = NodeSpec(
    id="parse-workflow",
    name="Parse Workflow",
    description="Parse and validate the workflow definition",
    node_type="llm_generate",
    input_keys=["workflow_definition", "input_data"],
    output_keys=["workflow_steps", "execution_plan", "dependencies"],
    system_prompt="""\
You are a workflow parser. Analyze the workflow definition and create an execution plan.

Workflow definition: {workflow_definition}
Input data: {input_data}

Parse the workflow to:
1. Extract all steps and their dependencies
2. Identify conditional branches
3. Detect parallel execution opportunities
4. Validate step inputs/outputs match

Output as JSON:
{{
  "workflow_steps": [
    {{"step_id": "...", "type": "...", "action": "...", "inputs": [...], "outputs": [...]}}
  ],
  "execution_plan": {{
    "total_steps": N,
    "estimated_duration_seconds": N,
    "parallel_stages": [[step_ids]]
  }},
  "dependencies": {{
    "step_id": ["depends_on_step_id"]
  }}
}}
""",
    tools=[],
    max_retries=2,
)

# ---------------------------------------------------------------------------
# Node 2: Execute workflow step
# ---------------------------------------------------------------------------
execute_step_node = NodeSpec(
    id="execute-step",
    name="Execute Step",
    description="Execute a single workflow step with appropriate tools",
    node_type="event_loop",
    input_keys=["current_step", "step_inputs", "available_tools"],
    output_keys=["step_result", "step_status", "step_outputs"],
    system_prompt="""\
You are a workflow executor. Execute the specified step.

Step: {current_step}
Inputs: {step_inputs}
Available tools: {available_tools}

Based on the step type, use the appropriate tools:
- api_call: Use web_search or HTTP requests
- data_transform: Transform data structures
- file_operation: Use file system tools
- notification: Send emails or messages
- condition_check: Evaluate conditions

Steps:
1. Validate inputs are present
2. Execute the step action
3. Validate outputs match expectations
4. Return results

Output as JSON:
{{
  "step_result": {{...}},
  "step_status": "success | failed | skipped",
  "step_outputs": {{
    "output_key": "value"
  }}
}}
""",
    tools=["web_search", "view_file", "write_to_file", "execute_command", "send_email"],
    max_retries=3,
)

# ---------------------------------------------------------------------------
# Node 3: Evaluate conditions
# ---------------------------------------------------------------------------
evaluate_conditions_node = NodeSpec(
    id="evaluate-conditions",
    name="Evaluate Conditions",
    description="Evaluate conditional branches to determine next steps",
    node_type="llm_generate",
    input_keys=["conditions", "current_state", "step_results"],
    output_keys=["next_steps", "branch_taken", "skip_steps"],
    system_prompt="""\
You are a condition evaluator. Determine which workflow branch to take.

Conditions: {conditions}
Current state: {current_state}
Step results: {step_results}

Evaluate each condition and determine:
1. Which conditions are satisfied
2. Which branch to execute
3. Which steps to skip

Common condition types:
- value_equals: Check if value matches
- value_greater_than: Numeric comparison
- field_exists: Check if field is present
- step_succeeded: Check if previous step succeeded
- custom_logic: Evaluate complex conditions

Output as JSON:
{{
  "next_steps": ["step_id1", "step_id2"],
  "branch_taken": "branch_name",
  "skip_steps": ["step_id3"]
}}
""",
    tools=[],
    max_retries=2,
)

# ---------------------------------------------------------------------------
# Node 4: Aggregate results
# ---------------------------------------------------------------------------
aggregate_results_node = NodeSpec(
    id="aggregate-results",
    name="Aggregate Results",
    description="Collect and combine results from all executed steps",
    node_type="llm_generate",
    input_keys=["all_step_results", "workflow_steps"],
    output_keys=["final_results", "execution_summary", "success_count", "failed_count"],
    system_prompt="""\
You are a results aggregator. Combine outputs from all workflow steps.

All step results: {all_step_results}
Workflow steps: {workflow_steps}

Aggregate the results:
1. Collect outputs from successful steps
2. Identify failed steps and errors
3. Calculate success/failure metrics
4. Combine outputs into final result

Output as JSON:
{{
  "final_results": {{
    "step_id": "output_value"
  }},
  "execution_summary": {{
    "total_steps": N,
    "executed": N,
    "skipped": N,
    "duration_seconds": N
  }},
  "success_count": N,
  "failed_count": N
}}
""",
    tools=[],
    max_retries=2,
)

# ---------------------------------------------------------------------------
# Node 5: Handle errors and retry
# ---------------------------------------------------------------------------
error_handler_node = NodeSpec(
    id="error-handler",
    name="Error Handler",
    description="Handle errors and determine retry strategy",
    node_type="llm_generate",
    input_keys=["failed_step", "error_details", "retry_policy"],
    output_keys=["should_retry", "retry_step", "fallback_action", "error_resolved"],
    system_prompt="""\
You are an error handler. Analyze the failure and determine recovery strategy.

Failed step: {failed_step}
Error: {error_details}
Retry policy: {retry_policy}

Determine the appropriate action:
- Retry with same inputs
- Retry with modified inputs
- Execute fallback step
- Skip and continue
- Fail entire workflow

Consider:
- Error type (transient vs permanent)
- Retry count and policy
- Availability of fallback options
- Impact on downstream steps

Output as JSON:
{{
  "should_retry": true/false,
  "retry_step": {{"step_id": "...", "modified_inputs": {{...}}}},
  "fallback_action": "skip | use_default | execute_fallback",
  "error_resolved": true/false
}}
""",
    tools=[],
    max_retries=2,
)

# All nodes for easy import
all_nodes = [
    parse_workflow_node,
    execute_step_node,
    evaluate_conditions_node,
    aggregate_results_node,
    error_handler_node,
]
