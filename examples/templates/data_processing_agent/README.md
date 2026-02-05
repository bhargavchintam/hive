# Data Processing Agent

A Hive agent that implements a complete ETL (Extract, Transform, Load) pipeline with validation for CSV and JSON data files.

## What This Template Demonstrates

- **Multi-stage data pipeline**: Load → Transform → Validate → Save
- **Event loop nodes**: Use tools for file I/O operations
- **Conditional edge routing**: Retry transformation if validation fails
- **Quality validation**: Configurable rules for data quality checks
- **Error handling**: Graceful degradation with detailed error reporting

## Agent Architecture

```
┌─────────────┐
│  load-data  │  (EventLoopNode: Load file, extract schema, validate structure)
└─────┬───────┘
      │ ON_SUCCESS
      v
┌─────────────────┐
│ transform-data  │  (LLMNode: Apply transformation rules)
└─────┬───────────┘
      │ ON_SUCCESS
      v
┌──────────────────┐
│ validate-output  │  (LLMNode: Check quality criteria)
└─────┬───────┬────┘
      │       │
      │       └─ CONDITIONAL (is_valid == False) ──┐
      │                                            │
      │ CONDITIONAL (is_valid == True)            │
      v                                            v
┌─────────────┐                          (Back to transform)
│  save-data  │  (EventLoopNode: Save to output format)
└─────────────┘
```

## Usage

### Basic Processing

```bash
# Process a CSV file with default settings
uv run python -m examples.templates.data_processing_agent process \
  --file-path "data/input.csv" \
  --output-path "data/output.csv"

# With transformation and quality rules
uv run python -m examples.templates.data_processing_agent process \
  --file-path "data/input.csv" \
  --output-path "data/cleaned.csv" \
  --rules '{
    "transformations": [
      {"type": "remove_duplicates"},
      {"type": "fill_missing", "strategy": "mean"},
      {"type": "filter", "condition": "age > 18"}
    ],
    "quality_checks": [
      {"type": "no_nulls", "columns": ["id", "email"]},
      {"type": "unique", "columns": ["id"]},
      {"type": "range", "column": "age", "min": 0, "max": 120}
    ]
  }'
```

### Batch Processing

```bash
# Process with full JSON config
uv run python -m examples.templates.data_processing_agent batch batch_config.json
```

Example `batch_config.json`:
```json
{
  "file_path": "data/customers.csv",
  "file_type": "csv",
  "transformation_rules": [
    {"type": "remove_duplicates"},
    {"type": "normalize_emails"},
    {"type": "fill_missing", "column": "phone", "value": "N/A"}
  ],
  "quality_rules": [
    {"type": "no_nulls", "columns": ["customer_id", "email"]},
    {"type": "email_format", "column": "email"},
    {"type": "unique", "columns": ["customer_id"]}
  ],
  "output_path": "data/customers_cleaned.csv",
  "output_format": "csv"
}
```

## Customization

### Adding New Transformation Rules

Edit `nodes/__init__.py` → `transform_data_node` → `system_prompt` to add custom transformation logic.

### Adding Quality Checks

Edit `nodes/__init__.py` → `validate_output_node` → `system_prompt` to add validation rules.

### Changing Retry Logic

Edit `agent.py` → `edges` to modify the validation retry behavior.

## Input Schema

```json
{
  "file_path": "string (required)",
  "file_type": "csv | json (required)",
  "transformation_rules": ["array of transformation objects"],
  "quality_rules": ["array of quality check objects"],
  "output_path": "string (required)",
  "output_format": "csv | json (required)"
}
```

## Output Schema

```json
{
  "final_data": ["processed data array"],
  "validation_report": {
    "total_checks": "number",
    "passed": "number",
    "failed": "number",
    "issues": ["array of issue descriptions"]
  },
  "saved_path": "string",
  "summary": {
    "rows_saved": "number",
    "file_size_kb": "number",
    "format": "string"
  }
}
```

## Common Transformation Rules

- `remove_duplicates` - Remove duplicate rows
- `fill_missing` - Fill null values (mean, median, mode, constant)
- `filter` - Filter rows by condition
- `rename_columns` - Rename column headers
- `convert_types` - Convert data types
- `normalize` - Normalize value ranges
- `aggregate` - Group and aggregate data

## Common Quality Checks

- `no_nulls` - Ensure no null values in specified columns
- `unique` - Ensure uniqueness in specified columns
- `range` - Validate numeric ranges
- `format` - Validate string formats (email, phone, etc.)
- `referential_integrity` - Check foreign key relationships
- `completeness` - Ensure required fields are present

## Error Handling

The agent handles errors at multiple stages:

1. **Load errors**: Invalid file path, unsupported format, corrupted data
2. **Transformation errors**: Invalid rules, incompatible operations
3. **Validation errors**: Quality checks fail → automatic retry
4. **Save errors**: Permission issues, disk space

All errors include detailed messages in the output JSON.

## Example Use Cases

1. **Data Cleaning**: Remove duplicates, fill missing values, normalize formats
2. **Data Validation**: Ensure data quality before import to database
3. **ETL Pipeline**: Extract from source, transform for target system, load to destination
4. **Data Migration**: Convert between formats with validation
5. **Batch Processing**: Process multiple files with consistent rules

## Extending This Template

- **Add new data sources**: Extend load_data_node to support databases, APIs
- **Custom transformations**: Add domain-specific transformation logic
- **Advanced validation**: Implement statistical validation, ML-based anomaly detection
- **Reporting**: Generate detailed transformation and quality reports
- **Scheduling**: Integrate with cron or workflow orchestration tools
