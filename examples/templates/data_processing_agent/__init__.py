"""
Data Processing Agent - ETL pipeline with validation.

A Hive agent that loads, transforms, validates, and saves data files
with configurable transformation and quality rules.
"""

from .agent import DataProcessingAgent, default_agent, goal, graph

__all__ = ["DataProcessingAgent", "default_agent", "goal", "graph"]

__version__ = "1.0.0"
