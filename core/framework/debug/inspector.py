"""
State and node inspection utilities for debugging.

Provides tools to inspect:
- Node inputs and outputs
- Execution state at any point
- Variable values and types
- Graph structure and connectivity
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from framework.graph import GraphSpec, NodeSpec


@dataclass
class NodeExecutionInfo:
    """Information about a node execution."""

    node_id: str
    node_name: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    status: str  # success, failed, skipped
    duration_ms: float
    error: Optional[str] = None


class NodeInspector:
    """
    Inspector for node-level debugging.

    Provides detailed information about node execution,
    inputs, outputs, and status.
    """

    def __init__(self, graph: GraphSpec):
        """
        Initialize the inspector.

        Args:
            graph: The graph spec to inspect
        """
        self.graph = graph
        self.node_map = {node.id: node for node in graph.nodes}
        self.execution_history: list[NodeExecutionInfo] = []

    def inspect_node(self, node_id: str) -> dict[str, Any]:
        """
        Get detailed information about a node.

        Args:
            node_id: ID of the node to inspect

        Returns:
            Dictionary with node information
        """
        if node_id not in self.node_map:
            return {"error": f"Node '{node_id}' not found"}

        node = self.node_map[node_id]

        return {
            "id": node.id,
            "name": node.name,
            "description": node.description,
            "node_type": node.node_type,
            "input_keys": node.input_keys,
            "output_keys": node.output_keys,
            "tools": getattr(node, "tools", []),
            "max_retries": getattr(node, "max_retries", 0),
            "system_prompt_preview": self._preview_text(
                getattr(node, "system_prompt", ""), 200
            ),
        }

    def inspect_node_inputs(
        self, node_id: str, context: dict
    ) -> dict[str, Any]:
        """
        Inspect inputs for a node from the current context.

        Args:
            node_id: ID of the node
            context: Current execution context

        Returns:
            Dictionary of input values
        """
        if node_id not in self.node_map:
            return {"error": f"Node '{node_id}' not found"}

        node = self.node_map[node_id]
        inputs = {}

        for key in node.input_keys:
            if key in context:
                value = context[key]
                inputs[key] = {
                    "value": self._preview_value(value),
                    "type": type(value).__name__,
                    "size": self._get_size(value),
                }
            else:
                inputs[key] = {"status": "missing", "required": True}

        return inputs

    def inspect_node_outputs(
        self, node_id: str, context: dict
    ) -> dict[str, Any]:
        """
        Inspect outputs from a node in the current context.

        Args:
            node_id: ID of the node
            context: Current execution context

        Returns:
            Dictionary of output values
        """
        if node_id not in self.node_map:
            return {"error": f"Node '{node_id}' not found"}

        node = self.node_map[node_id]
        outputs = {}

        for key in node.output_keys:
            if key in context:
                value = context[key]
                outputs[key] = {
                    "value": self._preview_value(value),
                    "type": type(value).__name__,
                    "size": self._get_size(value),
                }
            else:
                outputs[key] = {"status": "not_produced"}

        return outputs

    def record_execution(self, info: NodeExecutionInfo):
        """Record a node execution for history."""
        self.execution_history.append(info)

    def get_execution_history(self, node_id: Optional[str] = None) -> list[NodeExecutionInfo]:
        """
        Get execution history for a specific node or all nodes.

        Args:
            node_id: Optional node ID to filter by

        Returns:
            List of execution records
        """
        if node_id:
            return [e for e in self.execution_history if e.node_id == node_id]
        return self.execution_history.copy()

    def _preview_value(self, value: Any, max_length: int = 100) -> Any:
        """Create a preview of a value for display."""
        if isinstance(value, str):
            return self._preview_text(value, max_length)
        elif isinstance(value, (list, tuple)):
            if len(value) > 5:
                return f"[{len(value)} items] {value[:2]}..."
            return value
        elif isinstance(value, dict):
            if len(value) > 5:
                keys = list(value.keys())[:3]
                return f"{{{len(value)} keys}} {keys}..."
            return value
        else:
            return value

    def _preview_text(self, text: str, max_length: int) -> str:
        """Preview text with truncation."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def _get_size(self, value: Any) -> str:
        """Get a human-readable size for a value."""
        if isinstance(value, str):
            return f"{len(value)} chars"
        elif isinstance(value, (list, tuple)):
            return f"{len(value)} items"
        elif isinstance(value, dict):
            return f"{len(value)} keys"
        else:
            return "N/A"


class StateInspector:
    """
    Inspector for execution state.

    Provides tools to inspect the complete state
    at any point during execution.
    """

    def __init__(self):
        """Initialize the state inspector."""
        self.snapshots: list[dict] = []

    def take_snapshot(self, step: int, node_id: str, context: dict) -> dict:
        """
        Take a snapshot of the current state.

        Args:
            step: Current step number
            node_id: Current node ID
            context: Current execution context

        Returns:
            Snapshot dictionary
        """
        snapshot = {
            "step": step,
            "node_id": node_id,
            "timestamp": self._get_timestamp(),
            "context_keys": list(context.keys()),
            "context_preview": {
                k: self._preview_value(v)
                for k, v in context.items()
            },
        }

        self.snapshots.append(snapshot)
        return snapshot

    def get_snapshot(self, step: int) -> Optional[dict]:
        """Get a specific snapshot by step number."""
        for snapshot in self.snapshots:
            if snapshot["step"] == step:
                return snapshot
        return None

    def get_all_snapshots(self) -> list[dict]:
        """Get all snapshots."""
        return self.snapshots.copy()

    def compare_snapshots(self, step1: int, step2: int) -> dict:
        """
        Compare two snapshots to see what changed.

        Args:
            step1: First step number
            step2: Second step number

        Returns:
            Dictionary of differences
        """
        snap1 = self.get_snapshot(step1)
        snap2 = self.get_snapshot(step2)

        if not snap1 or not snap2:
            return {"error": "One or both snapshots not found"}

        keys1 = set(snap1["context_keys"])
        keys2 = set(snap2["context_keys"])

        return {
            "added_keys": list(keys2 - keys1),
            "removed_keys": list(keys1 - keys2),
            "common_keys": list(keys1 & keys2),
            "step_diff": step2 - step1,
        }

    def format_snapshot(self, snapshot: dict) -> str:
        """Format a snapshot for display."""
        lines = [
            "=" * 70,
            f"SNAPSHOT - Step {snapshot['step']}",
            "=" * 70,
            f"Node: {snapshot['node_id']}",
            f"Timestamp: {snapshot['timestamp']}",
            f"\nContext ({len(snapshot['context_keys'])} keys):",
        ]

        for key, value in snapshot["context_preview"].items():
            lines.append(f"  {key}: {value}")

        lines.append("=" * 70)
        return "\n".join(lines)

    def _preview_value(self, value: Any, max_length: int = 80) -> str:
        """Preview a value as a string."""
        try:
            if isinstance(value, str):
                if len(value) > max_length:
                    return f'"{value[:max_length]}..."'
                return f'"{value}"'
            elif isinstance(value, (list, tuple)):
                if len(value) > 3:
                    return f"[{len(value)} items]"
                return str(value)
            elif isinstance(value, dict):
                if len(value) > 3:
                    return f"{{{len(value)} keys}}"
                return str(value)
            else:
                return str(value)
        except Exception:
            return "<unprintable>"

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
