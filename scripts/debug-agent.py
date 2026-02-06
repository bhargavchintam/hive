#!/usr/bin/env python3
"""
Agent Debugging CLI

Interactive debugging tool for Hive agents.

Usage:
    # Visualize graph structure
    python scripts/debug-agent.py visualize exports/my_agent/agent.json

    # Run with interactive debugging
    python scripts/debug-agent.py debug exports/my_agent/agent.json \
        --input '{"data": "value"}' \
        --breakpoint load-data

    # Analyze execution trace
    python scripts/debug-agent.py trace exports/my_agent/agent.json \
        --input '{"data": "value"}'

    # Inspect nodes
    python scripts/debug-agent.py inspect exports/my_agent/agent.json \
        --node transform-data
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "core"))

from framework.debug import (
    AgentDebugger,
    BreakpointType,
    GraphVisualizer,
    NodeInspector,
    ToolCallTracer,
    EdgeRouteVisualizer,
)


def load_agent_spec(agent_json_path: str) -> tuple:
    """Load agent specification from JSON file."""
    with open(agent_json_path) as f:
        spec = json.load(f)

    # This is simplified - in production, use proper agent loading
    graph = spec.get("graph")
    goal = spec.get("goal")

    if not graph:
        raise ValueError("Agent spec must contain 'graph'")

    return graph, goal


def cmd_visualize(args):
    """Visualize agent graph structure."""
    print(f"📊 Visualizing agent: {args.agent_json}\n")

    graph, _ = load_agent_spec(args.agent_json)
    visualizer = GraphVisualizer(graph)

    if args.format == "ascii":
        print(visualizer.render_ascii())
    elif args.format == "mermaid":
        print(visualizer.render_mermaid())
    elif args.format == "dot":
        print(visualizer.render_dot())

    # Show connectivity if node specified
    if args.node:
        print(f"\n🔗 Connectivity for {args.node}:")
        connectivity = visualizer.get_node_connectivity(args.node)
        print(json.dumps(connectivity, indent=2))

    # Show execution paths if requested
    if args.show_paths:
        print(f"\n🛤️  Possible execution paths:")
        paths = visualizer.find_execution_paths(max_depth=args.max_depth)
        for i, path in enumerate(paths, 1):
            print(f"{i}. {' → '.join(path)}")


async def cmd_debug(args):
    """Run agent with interactive debugging."""
    print(f"🐛 Debugging agent: {args.agent_json}\n")

    graph, goal = load_agent_spec(args.agent_json)

    # Parse input
    context = {}
    if args.input:
        try:
            context = json.loads(args.input)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing input JSON: {e}")
            sys.exit(1)

    # This would require full Runtime integration
    # Simplified for demonstration
    print("⚠️  Note: Full debugging requires Runtime integration")
    print("This is a demonstration of the debugging API.\n")

    # Show what debugging would do
    print("Debugging configuration:")
    print(f"  Interactive mode: {args.interactive}")
    if args.breakpoint:
        print(f"  Breakpoints: {args.breakpoint}")
    print(f"  Step mode: {args.step}")
    print(f"\nInput context: {json.dumps(context, indent=2)}")

    # In production, this would be:
    # runtime = Runtime(graph=graph, goal=goal, ...)
    # debugger = AgentDebugger(runtime, interactive=args.interactive)
    # if args.breakpoint:
    #     for bp in args.breakpoint:
    #         debugger.set_breakpoint(bp, BreakpointType.NODE_ENTER)
    # result = await debugger.run_with_debugging(context)


async def cmd_trace(args):
    """Run agent and show execution trace."""
    print(f"🔍 Tracing agent execution: {args.agent_json}\n")

    graph, goal = load_agent_spec(args.agent_json)

    # Parse input
    context = {}
    if args.input:
        try:
            context = json.loads(args.input)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing input JSON: {e}")
            sys.exit(1)

    # Set up tracer
    tracer = ToolCallTracer(enable_timing=True)
    trace = tracer.start_trace("cli-trace-1")

    print("⚠️  Note: Full tracing requires Runtime integration")
    print("This demonstrates the tracing API.\n")

    # In production, integrate with Runtime
    # runtime = Runtime(graph=graph, goal=goal, ...)
    # result = await runtime.execute(context)

    # Show example trace format
    print("Trace format example:")
    print(tracer.format_trace(trace))

    if args.stats:
        print("\nTool call statistics:")
        print(json.dumps(tracer.get_tool_call_stats(), indent=2))


def cmd_inspect(args):
    """Inspect node details."""
    print(f"🔍 Inspecting agent nodes: {args.agent_json}\n")

    graph, _ = load_agent_spec(args.agent_json)
    inspector = NodeInspector(graph)

    if args.node:
        # Inspect specific node
        print(f"Node: {args.node}\n")
        info = inspector.inspect_node(args.node)
        print(json.dumps(info, indent=2))

        # Show connectivity
        visualizer = GraphVisualizer(graph)
        connectivity = visualizer.get_node_connectivity(args.node)
        print(f"\nConnectivity:")
        print(f"  Incoming edges: {len(connectivity['incoming_edges'])}")
        for edge in connectivity['incoming_edges']:
            print(f"    ← {edge['source']} (via {edge['edge_id']})")
        print(f"  Outgoing edges: {len(connectivity['outgoing_edges'])}")
        for edge in connectivity['outgoing_edges']:
            print(f"    → {edge['target']} (via {edge['edge_id']})")
    else:
        # List all nodes
        print("All nodes:\n")
        for node in graph.nodes:
            print(f"  • {node.id}")
            print(f"      Name: {node.name}")
            print(f"      Type: {node.node_type}")
            print(f"      Inputs: {', '.join(node.input_keys)}")
            print(f"      Outputs: {', '.join(node.output_keys)}")
            print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Agent Debugging CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize graph as ASCII art
  python scripts/debug-agent.py visualize exports/my_agent/agent.json

  # Visualize as Mermaid diagram
  python scripts/debug-agent.py visualize exports/my_agent/agent.json --format mermaid

  # Run with interactive debugging
  python scripts/debug-agent.py debug exports/my_agent/agent.json \\
      --input '{"data": "value"}' --interactive --breakpoint load-data

  # Trace execution
  python scripts/debug-agent.py trace exports/my_agent/agent.json \\
      --input '{"data": "value"}' --stats

  # Inspect specific node
  python scripts/debug-agent.py inspect exports/my_agent/agent.json --node transform-data

  # List all nodes
  python scripts/debug-agent.py inspect exports/my_agent/agent.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Visualize command
    vis_parser = subparsers.add_parser("visualize", help="Visualize agent graph")
    vis_parser.add_argument("agent_json", help="Path to agent.json file")
    vis_parser.add_argument(
        "--format",
        choices=["ascii", "mermaid", "dot"],
        default="ascii",
        help="Visualization format",
    )
    vis_parser.add_argument("--node", help="Show connectivity for specific node")
    vis_parser.add_argument(
        "--show-paths", action="store_true", help="Show all possible execution paths"
    )
    vis_parser.add_argument("--max-depth", type=int, default=10, help="Max path depth")

    # Debug command
    debug_parser = subparsers.add_parser("debug", help="Run with interactive debugging")
    debug_parser.add_argument("agent_json", help="Path to agent.json file")
    debug_parser.add_argument("--input", "-i", help="JSON input context")
    debug_parser.add_argument(
        "--breakpoint", "-b", action="append", help="Set breakpoint on node"
    )
    debug_parser.add_argument(
        "--interactive", action="store_true", help="Enable interactive mode"
    )
    debug_parser.add_argument("--step", action="store_true", help="Enable step mode")

    # Trace command
    trace_parser = subparsers.add_parser("trace", help="Trace agent execution")
    trace_parser.add_argument("agent_json", help="Path to agent.json file")
    trace_parser.add_argument("--input", "-i", help="JSON input context")
    trace_parser.add_argument("--stats", action="store_true", help="Show statistics")

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect node details")
    inspect_parser.add_argument("agent_json", help="Path to agent.json file")
    inspect_parser.add_argument("--node", "-n", help="Node ID to inspect")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "visualize":
        cmd_visualize(args)
    elif args.command == "debug":
        asyncio.run(cmd_debug(args))
    elif args.command == "trace":
        asyncio.run(cmd_trace(args))
    elif args.command == "inspect":
        cmd_inspect(args)


if __name__ == "__main__":
    main()
