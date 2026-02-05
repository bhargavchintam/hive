"""Runtime configuration for Workflow Automation Agent."""

from dataclasses import dataclass


@dataclass
class RuntimeConfig:
    """Configuration for agent execution."""

    model: str = "anthropic/claude-sonnet-4"
    mock_mode: bool = False
    verbose: bool = False
    debug: bool = False


# Default configuration instance
default_config = RuntimeConfig()
