"""
Main debugger class with step-through execution and breakpoints.

Provides interactive debugging capabilities for Hive agents:
- Set breakpoints on nodes, edges, or conditions
- Step through execution one node at a time
- Inspect state at each step
- Continue execution to next breakpoint
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from framework.graph import GraphSpec, NodeSpec
from framework.runtime.core import Runtime


class BreakpointType(Enum):
    """Type of breakpoint."""

    NODE_ENTER = "node_enter"  # Break when entering a node
    NODE_EXIT = "node_exit"  # Break when exiting a node
    EDGE_TRAVERSE = "edge_traverse"  # Break when traversing an edge
    CONDITION_EVAL = "condition_eval"  # Break when evaluating a condition
    TOOL_CALL = "tool_call"  # Break before tool execution
    ERROR = "error"  # Break on errors


@dataclass
class Breakpoint:
    """Represents a debugging breakpoint."""

    id: str
    breakpoint_type: BreakpointType
    target: str  # node_id, edge_id, tool_name, etc.
    condition: Optional[str] = None  # Optional condition expression
    enabled: bool = True
    hit_count: int = 0


@dataclass
class DebugState:
    """Current debugging state."""

    current_node: Optional[str] = None
    current_edge: Optional[str] = None
    context: dict = field(default_factory=dict)
    step_count: int = 0
    tool_calls: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    paused: bool = False


class AgentDebugger:
    """
    Interactive debugger for Hive agents.

    Provides step-through execution, breakpoints, and state inspection.

    Example:
        debugger = AgentDebugger(runtime)
        debugger.set_breakpoint("process-data", BreakpointType.NODE_ENTER)
        result = await debugger.run_with_debugging(context)
    """

    def __init__(self, runtime: Runtime, interactive: bool = False):
        """
        Initialize the debugger.

        Args:
            runtime: The Runtime instance to debug
            interactive: If True, wait for user input at breakpoints
        """
        self.runtime = runtime
        self.interactive = interactive
        self.breakpoints: dict[str, Breakpoint] = {}
        self.state = DebugState()
        self.step_mode = False
        self.trace_history: list[dict] = []

        # Callbacks for debugging events
        self.on_breakpoint_hit: Optional[Callable] = None
        self.on_step_complete: Optional[Callable] = None
        self.on_node_enter: Optional[Callable] = None
        self.on_node_exit: Optional[Callable] = None

    def set_breakpoint(
        self,
        target: str,
        breakpoint_type: BreakpointType = BreakpointType.NODE_ENTER,
        condition: Optional[str] = None,
    ) -> Breakpoint:
        """
        Set a breakpoint.

        Args:
            target: Target node_id, edge_id, or tool_name
            breakpoint_type: Type of breakpoint
            condition: Optional condition expression

        Returns:
            The created breakpoint
        """
        bp_id = f"{breakpoint_type.value}:{target}"
        breakpoint = Breakpoint(
            id=bp_id,
            breakpoint_type=breakpoint_type,
            target=target,
            condition=condition,
        )
        self.breakpoints[bp_id] = breakpoint
        return breakpoint

    def remove_breakpoint(self, bp_id: str) -> bool:
        """Remove a breakpoint by ID."""
        if bp_id in self.breakpoints:
            del self.breakpoints[bp_id]
            return True
        return False

    def list_breakpoints(self) -> list[Breakpoint]:
        """List all breakpoints."""
        return list(self.breakpoints.values())

    def enable_step_mode(self):
        """Enable step-by-step execution."""
        self.step_mode = True

    def disable_step_mode(self):
        """Disable step-by-step execution."""
        self.step_mode = False

    def _should_break(self, breakpoint_type: BreakpointType, target: str, context: dict) -> bool:
        """Check if we should break at this point."""
        bp_id = f"{breakpoint_type.value}:{target}"
        if bp_id not in self.breakpoints:
            return False

        breakpoint = self.breakpoints[bp_id]
        if not breakpoint.enabled:
            return False

        # Check condition if specified
        if breakpoint.condition:
            try:
                # Simple eval - in production, use safer evaluation
                if not eval(breakpoint.condition, {"context": context}):
                    return False
            except Exception:
                return False

        breakpoint.hit_count += 1
        return True

    async def _pause_at_breakpoint(self, breakpoint: Breakpoint, state: dict):
        """Pause execution at a breakpoint."""
        self.state.paused = True

        if self.on_breakpoint_hit:
            await self.on_breakpoint_hit(breakpoint, state)

        if self.interactive:
            print(f"\n🔴 Breakpoint hit: {breakpoint.id}")
            print(f"   Type: {breakpoint.breakpoint_type.value}")
            print(f"   Target: {breakpoint.target}")
            print(f"   Hit count: {breakpoint.hit_count}")
            print(f"\nCurrent state:")
            print(f"   Node: {self.state.current_node}")
            print(f"   Step: {self.state.step_count}")
            print(f"\nCommands: (c)ontinue, (s)tep, (i)nspect, (q)uit")

            # Wait for user input
            command = input("debugger> ").strip().lower()

            if command == "c":
                self.state.paused = False
            elif command == "s":
                self.step_mode = True
                self.state.paused = False
            elif command == "i":
                self._print_state()
                await self._pause_at_breakpoint(breakpoint, state)  # Re-pause
            elif command == "q":
                raise KeyboardInterrupt("Debugging stopped by user")
        else:
            self.state.paused = False

    def _print_state(self):
        """Print current debugging state."""
        print("\n" + "=" * 70)
        print("DEBUGGING STATE")
        print("=" * 70)
        print(f"\nCurrent node: {self.state.current_node}")
        print(f"Step count: {self.state.step_count}")
        print(f"Tool calls: {len(self.state.tool_calls)}")
        print(f"Errors: {len(self.state.errors)}")
        print(f"\nContext keys: {list(self.state.context.keys())}")
        print("\nRecent trace:")
        for entry in self.trace_history[-5:]:
            print(f"  - {entry.get('event')}: {entry.get('target')}")
        print("=" * 70 + "\n")

    async def run_with_debugging(self, context: dict) -> dict:
        """
        Run the agent with debugging enabled.

        Args:
            context: Input context for the agent

        Returns:
            Execution result
        """
        self.state.context = context.copy()
        self.state.step_count = 0
        self.trace_history.clear()

        # Wrap the runtime execution with debugging hooks
        # This is a simplified version - in production, integrate with Runtime events
        try:
            result = await self.runtime.execute(context)
            return result
        except KeyboardInterrupt:
            print("\n🛑 Debugging stopped")
            return {"status": "debugging_stopped", "state": self.state}

    async def step(self) -> dict:
        """
        Execute a single step.

        Returns:
            State after the step
        """
        self.enable_step_mode()
        # Execute one node and return
        # This requires integration with Runtime internals
        return {
            "current_node": self.state.current_node,
            "step_count": self.state.step_count,
            "context": self.state.context,
        }

    def get_trace_history(self) -> list[dict]:
        """Get execution trace history."""
        return self.trace_history.copy()

    def get_state(self) -> DebugState:
        """Get current debugging state."""
        return self.state

    def reset(self):
        """Reset debugger state."""
        self.state = DebugState()
        self.trace_history.clear()
        for bp in self.breakpoints.values():
            bp.hit_count = 0
