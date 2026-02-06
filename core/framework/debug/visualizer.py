"""
Graph and edge routing visualization utilities.

Provides visualization tools for:
- Graph structure (nodes and edges)
- Execution paths
- Edge routing decisions
- Node connectivity
"""

from __future__ import annotations

from typing import Any, Optional

from framework.graph import EdgeSpec, GraphSpec, NodeSpec


class GraphVisualizer:
    """
    Visualizer for graph structure.

    Creates text-based and diagram representations
    of agent graphs for debugging and documentation.
    """

    def __init__(self, graph: GraphSpec):
        """
        Initialize the visualizer.

        Args:
            graph: The graph spec to visualize
        """
        self.graph = graph
        self.node_map = {node.id: node for node in graph.nodes}
        self.edge_map = {edge.id: edge for edge in graph.edges}

    def render_ascii(self) -> str:
        """
        Render the graph as ASCII art.

        Returns:
            ASCII representation of the graph
        """
        lines = [
            "=" * 70,
            "GRAPH STRUCTURE",
            "=" * 70,
            f"\nEntry point: {self.graph.entry_point}",
            f"Nodes: {len(self.graph.nodes)}",
            f"Edges: {len(self.graph.edges)}",
            "\n" + "-" * 70,
        ]

        # Group edges by source
        edges_by_source = {}
        for edge in self.graph.edges:
            if edge.source not in edges_by_source:
                edges_by_source[edge.source] = []
            edges_by_source[edge.source].append(edge)

        # Render each node with its outgoing edges
        for node in self.graph.nodes:
            lines.append(f"\n┌─ {node.id}")
            lines.append(f"│  Name: {node.name}")
            lines.append(f"│  Type: {node.node_type}")

            # Show outgoing edges
            if node.id in edges_by_source:
                lines.append("│  Outgoing edges:")
                for edge in edges_by_source[node.id]:
                    condition = edge.condition.value if hasattr(edge.condition, 'value') else edge.condition
                    lines.append(f"│    → {edge.target} (via {edge.id}, {condition})")
            else:
                lines.append("│  No outgoing edges (terminal node)")

            lines.append("└" + "─" * 68)

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    def render_mermaid(self) -> str:
        """
        Render the graph as Mermaid diagram syntax.

        Returns:
            Mermaid diagram code
        """
        lines = [
            "```mermaid",
            "graph TD",
        ]

        # Add nodes
        for node in self.graph.nodes:
            node_label = f"{node.name}\\n({node.node_type})"
            if node.id == self.graph.entry_point:
                # Entry point - double circle
                lines.append(f'    {node.id}(("{node_label}"))')
            else:
                # Regular node - rectangle
                lines.append(f'    {node.id}["{node_label}"]')

        # Add edges
        for edge in self.graph.edges:
            condition = edge.condition.value if hasattr(edge.condition, 'value') else edge.condition
            edge_label = f"{condition}"

            if hasattr(edge, 'condition_expr') and edge.condition_expr:
                edge_label += f"\\n{edge.condition_expr}"

            lines.append(f'    {edge.source} -->|"{edge_label}"| {edge.target}')

        lines.append("```")
        return "\n".join(lines)

    def render_dot(self) -> str:
        """
        Render the graph in Graphviz DOT format.

        Returns:
            DOT format string
        """
        lines = [
            "digraph Agent {",
            "    rankdir=TD;",
            "    node [shape=box, style=rounded];",
            "",
        ]

        # Add nodes
        for node in self.graph.nodes:
            label = f"{node.name}\\n({node.node_type})"
            attrs = ['label="{}"'.format(label)]

            if node.id == self.graph.entry_point:
                attrs.append('style="rounded,bold"')
                attrs.append('color="blue"')

            lines.append(f'    {node.id} [{", ".join(attrs)}];')

        lines.append("")

        # Add edges
        for edge in self.graph.edges:
            condition = edge.condition.value if hasattr(edge.condition, 'value') else str(edge.condition)
            label = condition

            if hasattr(edge, 'condition_expr') and edge.condition_expr:
                label += f"\\n{edge.condition_expr}"

            attrs = ['label="{}"'.format(label)]

            # Style by condition type
            if "CONDITIONAL" in condition:
                attrs.append('style="dashed"')

            lines.append(f'    {edge.source} -> {edge.target} [{", ".join(attrs)}];')

        lines.append("}")
        return "\n".join(lines)

    def get_node_connectivity(self, node_id: str) -> dict[str, Any]:
        """
        Get connectivity information for a node.

        Args:
            node_id: ID of the node

        Returns:
            Dictionary with incoming and outgoing edges
        """
        incoming = []
        outgoing = []

        for edge in self.graph.edges:
            if edge.target == node_id:
                incoming.append({
                    "edge_id": edge.id,
                    "source": edge.source,
                    "condition": edge.condition.value if hasattr(edge.condition, 'value') else str(edge.condition),
                })

            if edge.source == node_id:
                outgoing.append({
                    "edge_id": edge.id,
                    "target": edge.target,
                    "condition": edge.condition.value if hasattr(edge.condition, 'value') else str(edge.condition),
                })

        return {
            "node_id": node_id,
            "incoming_edges": incoming,
            "outgoing_edges": outgoing,
            "is_entry_point": node_id == self.graph.entry_point,
            "is_terminal": len(outgoing) == 0,
        }

    def find_execution_paths(
        self,
        start_node: Optional[str] = None,
        max_depth: int = 10,
    ) -> list[list[str]]:
        """
        Find all possible execution paths through the graph.

        Args:
            start_node: Starting node (default: entry point)
            max_depth: Maximum path depth to prevent infinite loops

        Returns:
            List of paths (each path is a list of node IDs)
        """
        start = start_node or self.graph.entry_point
        paths = []

        def dfs(current: str, path: list[str], depth: int):
            if depth > max_depth:
                return

            path = path + [current]

            # Find outgoing edges
            outgoing = [e for e in self.graph.edges if e.source == current]

            if not outgoing:
                # Terminal node - save path
                paths.append(path)
            else:
                for edge in outgoing:
                    dfs(edge.target, path, depth + 1)

        dfs(start, [], 0)
        return paths


class EdgeRouteVisualizer:
    """
    Visualizer for edge routing decisions.

    Shows which edges were taken during execution
    and why certain routing decisions were made.
    """

    def __init__(self, graph: GraphSpec):
        """
        Initialize the visualizer.

        Args:
            graph: The graph spec to visualize
        """
        self.graph = graph
        self.edge_map = {edge.id: edge for edge in graph.edges}
        self.traversal_history: list[dict] = []

    def record_traversal(
        self,
        edge_id: str,
        context: dict,
        reason: str,
        skipped_edges: Optional[list[str]] = None,
    ):
        """
        Record an edge traversal.

        Args:
            edge_id: ID of the edge traversed
            context: Execution context at the time
            reason: Reason this edge was chosen
            skipped_edges: List of edge IDs that were not taken
        """
        self.traversal_history.append({
            "edge_id": edge_id,
            "reason": reason,
            "skipped_edges": skipped_edges or [],
            "context_snapshot": list(context.keys()),
        })

    def visualize_routing_decision(self, step: int) -> str:
        """
        Visualize a specific routing decision.

        Args:
            step: Step number to visualize

        Returns:
            Formatted visualization of the routing decision
        """
        if step >= len(self.traversal_history):
            return "Step not found in history"

        decision = self.traversal_history[step]
        edge = self.edge_map.get(decision["edge_id"])

        if not edge:
            return "Edge not found"

        lines = [
            "=" * 70,
            f"ROUTING DECISION - Step {step}",
            "=" * 70,
            f"\nEdge taken: {edge.id}",
            f"  {edge.source} → {edge.target}",
            f"  Condition: {edge.condition.value if hasattr(edge.condition, 'value') else edge.condition}",
            f"\nReason: {decision['reason']}",
        ]

        if decision["skipped_edges"]:
            lines.append(f"\nSkipped edges ({len(decision['skipped_edges'])}):")
            for skipped_id in decision["skipped_edges"]:
                skipped_edge = self.edge_map.get(skipped_id)
                if skipped_edge:
                    lines.append(f"  ✗ {skipped_id}: {skipped_edge.source} → {skipped_edge.target}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    def visualize_execution_path(self, node_sequence: list[str]) -> str:
        """
        Visualize the path taken through the graph.

        Args:
            node_sequence: Sequence of nodes visited

        Returns:
            Formatted visualization of the execution path
        """
        lines = [
            "=" * 70,
            "EXECUTION PATH",
            "=" * 70,
            "",
        ]

        for i, node_id in enumerate(node_sequence, 1):
            lines.append(f"{i}. {node_id}")

            if i < len(node_sequence):
                # Find the edge between this node and the next
                next_node = node_sequence[i]
                edges = [e for e in self.graph.edges if e.source == node_id and e.target == next_node]

                if edges:
                    edge = edges[0]
                    condition = edge.condition.value if hasattr(edge.condition, 'value') else edge.condition
                    lines.append(f"   ↓ via {edge.id} ({condition})")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    def get_edge_usage_stats(self) -> dict[str, Any]:
        """
        Get statistics about edge usage.

        Returns:
            Dictionary with edge traversal statistics
        """
        edge_counts = {}

        for traversal in self.traversal_history:
            edge_id = traversal["edge_id"]
            if edge_id not in edge_counts:
                edge_counts[edge_id] = 0
            edge_counts[edge_id] += 1

        return {
            "total_traversals": len(self.traversal_history),
            "unique_edges_used": len(edge_counts),
            "edge_counts": edge_counts,
            "most_used_edge": max(edge_counts.items(), key=lambda x: x[1]) if edge_counts else None,
        }
