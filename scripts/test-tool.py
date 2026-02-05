#!/usr/bin/env python3
"""
Tool Discovery & Testing Utility for Aden Hive Framework

This script helps developers discover, explore, and test MCP tools before
integrating them into agents.

Usage:
    # List all available tools
    python scripts/test-tool.py --list

    # Show tool details
    python scripts/test-tool.py --describe web_search

    # Test a tool
    python scripts/test-tool.py web_search --query "Hive agent framework"

    # Interactive mode
    python scripts/test-tool.py --interactive

    # Check credentials for a tool
    python scripts/test-tool.py --check-credentials web_search
"""

import argparse
import asyncio
import inspect
import json
import sys
from pathlib import Path
from typing import Any

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "tools" / "src"))
sys.path.insert(0, str(project_root / "core"))

from aden_tools.credentials import CREDENTIAL_SPECS, CredentialStoreAdapter
from fastmcp import FastMCP


class ToolDiscovery:
    """Tool discovery and testing utility."""

    def __init__(self):
        """Initialize tool discovery."""
        self.mcp = FastMCP("tool-tester")
        self.credentials = None
        self.tools = {}

        # Try to load credentials
        try:
            self.credentials = CredentialStoreAdapter.default()
        except Exception:
            pass  # Credentials not available

        # Register all tools
        self._register_tools()

    def _register_tools(self):
        """Register all available tools."""
        from aden_tools.tools import register_all_tools

        register_all_tools(self.mcp, credentials=self.credentials)

        # Extract tool information from internal tool manager
        # FastMCP stores tools in _tool_manager._tools
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
            for tool_name, tool_obj in self.mcp._tool_manager._tools.items():
                # Get the actual callable function
                tool_func = tool_obj.fn if hasattr(tool_obj, 'fn') else tool_obj

                self.tools[tool_name] = {
                    "name": tool_name,
                    "function": tool_func,
                    "description": (tool_obj.description if hasattr(tool_obj, 'description')
                                  else tool_func.__doc__ or "No description available"),
                    "signature": inspect.signature(tool_func) if callable(tool_func) else None,
                    "parameters": self._extract_parameters(tool_func) if callable(tool_func) else {},
                }

    def _extract_parameters(self, func) -> dict[str, Any]:
        """Extract parameter information from function."""
        sig = inspect.signature(func)
        params = {}

        for param_name, param in sig.parameters.items():
            param_info = {
                "required": param.default == inspect.Parameter.empty,
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
            }

            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default

            params[param_name] = param_info

        return params

    def list_tools(self, verbose: bool = False):
        """List all available tools."""
        print("\n" + "=" * 70)
        print("AVAILABLE TOOLS")
        print("=" * 70 + "\n")

        # Group tools by category
        categories = {
            "File System": ["view_file", "write_to_file", "list_dir", "replace_file_content",
                           "apply_diff", "apply_patch", "grep_search", "execute_command"],
            "Web": ["web_search", "web_scrape"],
            "Documents": ["pdf_read", "csv_tool"],
            "Integrations": ["github_tool", "email_tool", "hubspot_tool", "slack_tool"],
            "Data Management": ["save_data", "load_data", "list_data_files", "serve_file_to_user"],
            "Example": ["example_tool"],
        }

        for category, tool_names in categories.items():
            found_tools = [name for name in tool_names if name in self.tools]
            if found_tools:
                print(f"📁 {category}")
                for tool_name in found_tools:
                    tool = self.tools[tool_name]
                    desc = tool["description"].split("\n")[0].strip()
                    if len(desc) > 60:
                        desc = desc[:57] + "..."

                    # Check if needs credentials
                    needs_creds = self._needs_credentials(tool_name)
                    cred_status = " 🔒" if needs_creds else ""

                    print(f"  • {tool_name}{cred_status}")
                    if verbose:
                        print(f"    {desc}")
                print()

        print("Legend: 🔒 = Requires credentials")
        print(f"\nTotal: {len(self.tools)} tools available")
        print("\nUse --describe <tool_name> for detailed information")
        print()

    def describe_tool(self, tool_name: str):
        """Show detailed information about a tool."""
        if tool_name not in self.tools:
            print(f"❌ Tool '{tool_name}' not found")
            print(f"\nAvailable tools: {', '.join(sorted(self.tools.keys()))}")
            return

        tool = self.tools[tool_name]

        print("\n" + "=" * 70)
        print(f"TOOL: {tool_name}")
        print("=" * 70 + "\n")

        # Description
        print("Description:")
        print(tool["description"].strip())
        print()

        # Parameters
        if tool["parameters"]:
            print("Parameters:")
            for param_name, param_info in tool["parameters"].items():
                required = "required" if param_info["required"] else "optional"
                param_type = param_info["type"]
                default = f" (default: {param_info.get('default')})" if "default" in param_info else ""

                print(f"  • {param_name}: {param_type} [{required}]{default}")
            print()

        # Credential requirements
        needs_creds = self._needs_credentials(tool_name)
        if needs_creds:
            print("Credentials: 🔒 Required")
            cred_spec = self._get_credential_spec(tool_name)
            if cred_spec:
                print(f"  Provider: {cred_spec.credential_id}")
                print(f"  Description: {cred_spec.description}")
            print()

        # Usage example
        print("Usage Example:")
        print(f"  python scripts/test-tool.py {tool_name} [parameters]")
        print()

        # Check if tool is ready to use
        if needs_creds:
            has_creds = self._check_credentials(tool_name)
            if has_creds:
                print("Status: ✅ Ready to use (credentials configured)")
            else:
                print("Status: ⚠️  Credentials not configured")
                print(f"  Run: python scripts/test-tool.py --check-credentials {tool_name}")
        else:
            print("Status: ✅ Ready to use (no credentials required)")

        print()

    def _needs_credentials(self, tool_name: str) -> bool:
        """Check if tool needs credentials."""
        credential_tools = [
            "web_search", "github_tool", "email_tool",
            "hubspot_tool", "slack_tool"
        ]
        return tool_name in credential_tools

    def _get_credential_spec(self, tool_name: str):
        """Get credential specification for tool."""
        tool_to_spec = {
            "web_search": ["google_search", "brave_search"],
            "github_tool": ["github"],
            "email_tool": ["resend"],
            "hubspot_tool": ["hubspot"],
            "slack_tool": ["slack"],
        }

        spec_names = tool_to_spec.get(tool_name, [])
        for spec_name in spec_names:
            if spec_name in CREDENTIAL_SPECS:
                return CREDENTIAL_SPECS[spec_name]
        return None

    def _check_credentials(self, tool_name: str) -> bool:
        """Check if credentials are available for tool."""
        if not self._needs_credentials(tool_name):
            return True

        if not self.credentials:
            return False

        # Try to get credentials
        cred_spec = self._get_credential_spec(tool_name)
        if not cred_spec:
            return False

        try:
            creds = self.credentials.get_credential(cred_spec.credential_id)
            return bool(creds)
        except Exception:
            return False

    def check_credentials_command(self, tool_name: str):
        """Show credential status and help for a tool."""
        print("\n" + "=" * 70)
        print(f"CREDENTIAL CHECK: {tool_name}")
        print("=" * 70 + "\n")

        if not self._needs_credentials(tool_name):
            print(f"✅ Tool '{tool_name}' does not require credentials")
            return

        has_creds = self._check_credentials(tool_name)
        cred_spec = self._get_credential_spec(tool_name)

        if has_creds:
            print(f"✅ Credentials configured for '{tool_name}'")
            if cred_spec:
                print(f"   Provider: {cred_spec.credential_id}")
        else:
            print(f"⚠️  Credentials NOT configured for '{tool_name}'")
            print()

            if cred_spec:
                print(f"Required: {cred_spec.credential_id}")
                print(f"Description: {cred_spec.description}")
                print()

                print("Setup Instructions:")
                print(f"  1. Get API key from: {cred_spec.help_url}")
                print(f"  2. Set environment variable: {cred_spec.env_var}")
                print()
                print("Options:")
                print(f"  • Add to .env file:")
                print(f"    echo '{cred_spec.env_var}=your-api-key' >> .env")
                print()
                print(f"  • Or use credential store:")
                print(f"    # Use /hive-credentials skill in Claude Code")

        print()

    async def test_tool(self, tool_name: str, **kwargs):
        """Test a tool with given parameters."""
        if tool_name not in self.tools:
            print(f"❌ Tool '{tool_name}' not found")
            return

        print("\n" + "=" * 70)
        print(f"TESTING: {tool_name}")
        print("=" * 70 + "\n")

        # Check credentials
        if self._needs_credentials(tool_name):
            if not self._check_credentials(tool_name):
                print("⚠️  Warning: Credentials not configured")
                print(f"   Run: python scripts/test-tool.py --check-credentials {tool_name}")
                print()

        print("Parameters:")
        for key, value in kwargs.items():
            print(f"  {key}: {value}")
        print()

        print("Executing...")
        print("-" * 70)

        try:
            tool_func = self.tools[tool_name]["function"]
            result = await tool_func(**kwargs)

            print("\n" + "-" * 70)
            print("Result:")
            print()

            if isinstance(result, (dict, list)):
                print(json.dumps(result, indent=2))
            else:
                print(result)

            print()
            print("✅ Tool executed successfully")

        except Exception as e:
            print("\n" + "-" * 70)
            print(f"❌ Error: {type(e).__name__}: {e}")
            import traceback
            print("\nTraceback:")
            traceback.print_exc()

        print()

    def interactive_mode(self):
        """Run interactive tool exploration."""
        print("\n" + "=" * 70)
        print("INTERACTIVE TOOL TESTER")
        print("=" * 70 + "\n")
        print("Commands:")
        print("  list           - List all tools")
        print("  describe <tool> - Show tool details")
        print("  test <tool>     - Test a tool (will prompt for parameters)")
        print("  creds <tool>    - Check credentials")
        print("  exit           - Exit interactive mode")
        print()

        while True:
            try:
                command = input("tool-tester> ").strip()

                if not command:
                    continue

                if command == "exit":
                    print("Goodbye!")
                    break

                parts = command.split(maxsplit=1)
                cmd = parts[0]
                arg = parts[1] if len(parts) > 1 else None

                if cmd == "list":
                    self.list_tools(verbose=True)
                elif cmd == "describe" and arg:
                    self.describe_tool(arg)
                elif cmd == "test" and arg:
                    print("Interactive testing not yet implemented")
                    print(f"Use: python scripts/test-tool.py {arg} [parameters]")
                elif cmd == "creds" and arg:
                    self.check_credentials_command(arg)
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'list', 'describe <tool>', 'creds <tool>', or 'exit'")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Tool Discovery & Testing Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all tools
  python scripts/test-tool.py --list

  # Show tool details
  python scripts/test-tool.py --describe web_search

  # Test web search
  python scripts/test-tool.py web_search --query "Python agent frameworks"

  # Check credentials
  python scripts/test-tool.py --check-credentials github_tool

  # Interactive mode
  python scripts/test-tool.py --interactive
        """,
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available tools",
    )

    parser.add_argument(
        "--describe",
        metavar="TOOL",
        help="Show detailed information about a tool",
    )

    parser.add_argument(
        "--check-credentials",
        metavar="TOOL",
        help="Check credential status for a tool",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )

    parser.add_argument(
        "tool_name",
        nargs="?",
        help="Tool to test",
    )

    # Parse known args to allow tool-specific arguments
    args, unknown = parser.parse_known_args()

    # Initialize discovery
    discovery = ToolDiscovery()

    # Handle commands
    if args.list:
        discovery.list_tools(verbose=True)
    elif args.describe:
        discovery.describe_tool(args.describe)
    elif args.check_credentials:
        discovery.check_credentials_command(args.check_credentials)
    elif args.interactive:
        discovery.interactive_mode()
    elif args.tool_name:
        # Parse tool-specific arguments
        tool_parser = argparse.ArgumentParser()
        tool = discovery.tools.get(args.tool_name)

        if not tool:
            print(f"❌ Tool '{args.tool_name}' not found")
            print(f"\nAvailable tools: {', '.join(sorted(discovery.tools.keys()))}")
            sys.exit(1)

        # Add arguments based on tool parameters
        for param_name, param_info in tool["parameters"].items():
            tool_parser.add_argument(
                f"--{param_name}",
                required=param_info["required"],
                help=f"{param_info['type']} ({'required' if param_info['required'] else 'optional'})",
            )

        tool_args = tool_parser.parse_args(unknown)
        kwargs = {k: v for k, v in vars(tool_args).items() if v is not None}

        # Run async tool test
        asyncio.run(discovery.test_tool(args.tool_name, **kwargs))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
