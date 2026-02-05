"""
Workflow Automation Agent - Multi-step workflow orchestration.

A Hive agent that executes complex workflows with conditional branching,
dependency management, error handling, and result aggregation.
"""

from .agent import WorkflowAutomationAgent, default_agent, goal, graph

__all__ = ["WorkflowAutomationAgent", "default_agent", "goal", "graph"]

__version__ = "1.0.0"
