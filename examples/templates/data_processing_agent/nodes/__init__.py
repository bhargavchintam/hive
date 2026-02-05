"""Node definitions for Data Processing Agent."""

from framework.graph import NodeSpec

# ---------------------------------------------------------------------------
# Node 1: Load and validate input data
# ---------------------------------------------------------------------------
load_data_node = NodeSpec(
    id="load-data",
    name="Load Data",
    description="Load data from file and perform initial validation",
    node_type="event_loop",
    input_keys=["file_path", "file_type"],
    output_keys=["raw_data", "data_schema", "validation_errors"],
    system_prompt="""\
You are a data loading specialist. Load the data file and validate its structure.

File path: {file_path}
File type: {file_type}

Available tools:
- load_data: Load data from workspace storage
- csv_read: Read CSV files
- csv_info: Get CSV structure information

Steps:
1. Load the data using the appropriate tool
2. Inspect the structure and schema
3. Check for missing values, duplicates, or format issues
4. Return the raw data and any validation errors

Output as JSON:
{{
  "raw_data": [...],
  "data_schema": {{"columns": [...], "row_count": N}},
  "validation_errors": [...]
}}
""",
    tools=["load_data", "csv_read", "csv_info"],
    max_retries=2,
)

# ---------------------------------------------------------------------------
# Node 2: Transform data according to rules
# ---------------------------------------------------------------------------
transform_data_node = NodeSpec(
    id="transform-data",
    name="Transform Data",
    description="Apply transformation rules to clean and reshape data",
    node_type="llm_generate",
    input_keys=["raw_data", "transformation_rules"],
    output_keys=["transformed_data", "transformation_log"],
    system_prompt="""\
You are a data transformation specialist. Apply the specified transformation rules.

Raw data: {raw_data}
Transformation rules: {transformation_rules}

Apply each transformation rule and track what was changed. Common transformations:
- Remove duplicates
- Fill missing values
- Convert data types
- Rename columns
- Filter rows
- Aggregate data

Output as JSON:
{{
  "transformed_data": [...],
  "transformation_log": [
    {{"rule": "...", "applied": true, "rows_affected": N}}
  ]
}}
""",
    tools=[],
    max_retries=2,
)

# ---------------------------------------------------------------------------
# Node 3: Validate transformed data
# ---------------------------------------------------------------------------
validate_output_node = NodeSpec(
    id="validate-output",
    name="Validate Output",
    description="Validate transformed data meets quality criteria",
    node_type="llm_generate",
    input_keys=["transformed_data", "quality_rules"],
    output_keys=["is_valid", "validation_report", "final_data"],
    system_prompt="""\
You are a data quality specialist. Validate the transformed data against quality rules.

Transformed data: {transformed_data}
Quality rules: {quality_rules}

Check for:
- Data type consistency
- Value ranges
- Required fields
- Referential integrity
- Business rule compliance

Output as JSON:
{{
  "is_valid": true/false,
  "validation_report": {{
    "total_checks": N,
    "passed": N,
    "failed": N,
    "issues": [...]
  }},
  "final_data": [...]
}}
""",
    tools=[],
    max_retries=2,
)

# ---------------------------------------------------------------------------
# Node 4: Save processed data
# ---------------------------------------------------------------------------
save_data_node = NodeSpec(
    id="save-data",
    name="Save Data",
    description="Save validated data to output file",
    node_type="event_loop",
    input_keys=["final_data", "output_path", "output_format"],
    output_keys=["saved_path", "summary"],
    system_prompt="""\
You are a data export specialist. Save the processed data to the specified output.

Final data: {final_data}
Output path: {output_path}
Output format: {output_format}

Available tools:
- save_data: Save data to workspace storage
- csv_write: Write data to CSV file

Steps:
1. Format the data for the specified output format
2. Save to the output path
3. Return confirmation and summary

Output as JSON:
{{
  "saved_path": "...",
  "summary": {{
    "rows_saved": N,
    "file_size_kb": N,
    "format": "..."
  }}
}}
""",
    tools=["save_data", "csv_write"],
    max_retries=2,
)

# All nodes for easy import
all_nodes = [
    load_data_node,
    transform_data_node,
    validate_output_node,
    save_data_node,
]
