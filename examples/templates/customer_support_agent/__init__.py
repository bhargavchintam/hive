"""
Customer Support Agent - Automated ticket classification and response.

A Hive agent that classifies support tickets, searches knowledge bases,
generates responses, and escalates complex cases to human agents.
"""

from .agent import CustomerSupportAgent, default_agent, goal, graph

__all__ = ["CustomerSupportAgent", "default_agent", "goal", "graph"]

__version__ = "1.0.0"
