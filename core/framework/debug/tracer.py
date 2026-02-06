"""
Tool call and execution tracing utilities.

Provides detailed tracing of:
- Tool invocations with arguments
- Tool execution timing
- Tool results and errors
- Call stack and nesting
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ToolCall:
    """Record of a single tool invocation."""

    tool_name: str
    arguments: dict[str, Any]
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    status: str = "pending"  # pending, success, failed
    call_stack_depth: int = 0


@dataclass
class ExecutionTrace:
    """Complete trace of an execution path."""

    trace_id: str
    start_time: float
    end_time: Optional[float] = None
    node_sequence: list[str] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    edge_traversals: list[dict] = field(default_factory=list)
    total_duration_ms: Optional[float] = None


class ToolCallTracer:
    """
    Tracer for tool calls and execution timing.

    Records detailed information about tool invocations,
    timing, and results for debugging and optimization.
    """

    def __init__(self, enable_timing: bool = True):
        """
        Initialize the tracer.

        Args:
            enable_timing: Whether to record timing information
        """
        self.enable_timing = enable_timing
        self.current_trace: Optional[ExecutionTrace] = None
        self.traces: list[ExecutionTrace] = []
        self.active_tool_calls: list[ToolCall] = []
        self.call_stack_depth = 0

    def start_trace(self, trace_id: str) -> ExecutionTrace:
        """
        Start a new execution trace.

        Args:
            trace_id: Unique identifier for this trace

        Returns:
            The created trace
        """
        trace = ExecutionTrace(
            trace_id=trace_id,
            start_time=time.time(),
        )
        self.current_trace = trace
        self.traces.append(trace)
        return trace

    def end_trace(self) -> Optional[ExecutionTrace]:
        """
        End the current trace.

        Returns:
            The completed trace, or None if no active trace
        """
        if not self.current_trace:
            return None

        self.current_trace.end_time = time.time()
        if self.current_trace.start_time:
            duration = (self.current_trace.end_time - self.current_trace.start_time) * 1000
            self.current_trace.total_duration_ms = duration

        completed_trace = self.current_trace
        self.current_trace = None
        return completed_trace

    def record_node_enter(self, node_id: str):
        """Record entering a node."""
        if self.current_trace:
            self.current_trace.node_sequence.append(node_id)

    def start_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> ToolCall:
        """
        Start recording a tool call.

        Args:
            tool_name: Name of the tool being called
            arguments: Arguments passed to the tool

        Returns:
            The tool call record
        """
        tool_call = ToolCall(
            tool_name=tool_name,
            arguments=arguments.copy(),
            start_time=time.time(),
            call_stack_depth=self.call_stack_depth,
        )

        self.active_tool_calls.append(tool_call)
        self.call_stack_depth += 1

        if self.current_trace:
            self.current_trace.tool_calls.append(tool_call)

        return tool_call

    def end_tool_call(
        self,
        tool_call: ToolCall,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ):
        """
        End recording a tool call.

        Args:
            tool_call: The tool call to complete
            result: Optional result from the tool
            error: Optional error message if tool failed
        """
        tool_call.end_time = time.time()

        if tool_call.start_time and tool_call.end_time:
            tool_call.duration_ms = (tool_call.end_time - tool_call.start_time) * 1000

        if error:
            tool_call.status = "failed"
            tool_call.error = error
        else:
            tool_call.status = "success"
            tool_call.result = result

        if tool_call in self.active_tool_calls:
            self.active_tool_calls.remove(tool_call)

        self.call_stack_depth = max(0, self.call_stack_depth - 1)

    def record_edge_traversal(self, edge_id: str, source: str, target: str, condition: str):
        """
        Record an edge traversal.

        Args:
            edge_id: ID of the edge
            source: Source node ID
            target: Target node ID
            condition: Condition that triggered this edge
        """
        if not self.current_trace:
            return

        self.current_trace.edge_traversals.append({
            "edge_id": edge_id,
            "source": source,
            "target": target,
            "condition": condition,
            "timestamp": time.time(),
        })

    def get_tool_call_stats(self) -> dict[str, Any]:
        """
        Get statistics about tool calls.

        Returns:
            Dictionary with tool call statistics
        """
        if not self.current_trace:
            return {"error": "No active trace"}

        tool_calls = self.current_trace.tool_calls
        successful = [tc for tc in tool_calls if tc.status == "success"]
        failed = [tc for tc in tool_calls if tc.status == "failed"]

        # Calculate timing statistics
        durations = [tc.duration_ms for tc in tool_calls if tc.duration_ms is not None]

        stats = {
            "total_calls": len(tool_calls),
            "successful": len(successful),
            "failed": len(failed),
            "tools_used": list(set(tc.tool_name for tc in tool_calls)),
        }

        if durations:
            stats["timing"] = {
                "total_ms": sum(durations),
                "average_ms": sum(durations) / len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
            }

        # Per-tool statistics
        tool_stats = {}
        for tc in tool_calls:
            if tc.tool_name not in tool_stats:
                tool_stats[tc.tool_name] = {
                    "count": 0,
                    "success": 0,
                    "failed": 0,
                    "total_duration_ms": 0,
                }

            tool_stats[tc.tool_name]["count"] += 1
            if tc.status == "success":
                tool_stats[tc.tool_name]["success"] += 1
            elif tc.status == "failed":
                tool_stats[tc.tool_name]["failed"] += 1

            if tc.duration_ms:
                tool_stats[tc.tool_name]["total_duration_ms"] += tc.duration_ms

        stats["by_tool"] = tool_stats

        return stats

    def format_tool_call(self, tool_call: ToolCall) -> str:
        """Format a tool call for display."""
        indent = "  " * tool_call.call_stack_depth

        status_symbol = {
            "pending": "⏳",
            "success": "✅",
            "failed": "❌",
        }.get(tool_call.status, "❓")

        duration_str = ""
        if tool_call.duration_ms is not None:
            duration_str = f" ({tool_call.duration_ms:.2f}ms)"

        lines = [f"{indent}{status_symbol} {tool_call.tool_name}{duration_str}"]

        # Show arguments
        if tool_call.arguments:
            args_preview = str(tool_call.arguments)[:100]
            if len(str(tool_call.arguments)) > 100:
                args_preview += "..."
            lines.append(f"{indent}   Args: {args_preview}")

        # Show result or error
        if tool_call.error:
            lines.append(f"{indent}   Error: {tool_call.error}")
        elif tool_call.result is not None:
            result_preview = str(tool_call.result)[:100]
            if len(str(tool_call.result)) > 100:
                result_preview += "..."
            lines.append(f"{indent}   Result: {result_preview}")

        return "\n".join(lines)

    def format_trace(self, trace: ExecutionTrace) -> str:
        """Format a complete trace for display."""
        lines = [
            "=" * 70,
            f"EXECUTION TRACE: {trace.trace_id}",
            "=" * 70,
        ]

        if trace.total_duration_ms:
            lines.append(f"Duration: {trace.total_duration_ms:.2f}ms")

        lines.append(f"\nNode Sequence ({len(trace.node_sequence)} nodes):")
        for i, node_id in enumerate(trace.node_sequence, 1):
            lines.append(f"  {i}. {node_id}")

        lines.append(f"\nTool Calls ({len(trace.tool_calls)} calls):")
        for tool_call in trace.tool_calls:
            lines.append(self.format_tool_call(tool_call))

        if trace.edge_traversals:
            lines.append(f"\nEdge Traversals ({len(trace.edge_traversals)} edges):")
            for edge in trace.edge_traversals:
                lines.append(f"  {edge['source']} → {edge['target']} (via {edge['edge_id']})")

        lines.append("=" * 70)
        return "\n".join(lines)

    def get_all_traces(self) -> list[ExecutionTrace]:
        """Get all traces."""
        return self.traces.copy()

    def clear_traces(self):
        """Clear all traces."""
        self.traces.clear()
        self.current_trace = None
        self.active_tool_calls.clear()
        self.call_stack_depth = 0

    def export_trace_json(self, trace: ExecutionTrace) -> dict:
        """Export a trace as JSON-serializable dictionary."""
        return {
            "trace_id": trace.trace_id,
            "start_time": trace.start_time,
            "end_time": trace.end_time,
            "total_duration_ms": trace.total_duration_ms,
            "node_sequence": trace.node_sequence,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "arguments": tc.arguments,
                    "duration_ms": tc.duration_ms,
                    "status": tc.status,
                    "error": tc.error,
                }
                for tc in trace.tool_calls
            ],
            "edge_traversals": trace.edge_traversals,
        }
