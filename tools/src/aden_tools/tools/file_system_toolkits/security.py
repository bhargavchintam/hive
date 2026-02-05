import os

# Use user home directory for workspaces
WORKSPACES_DIR = os.path.expanduser("~/.hive/workdir/workspaces")


def get_secure_path(path: str, workspace_id: str, agent_id: str, session_id: str) -> str:
    """Resolve and verify a path within a 3-layer sandbox (workspace/agent/session).

    This function prevents path traversal attacks including symlink attacks by:
    1. Resolving all symlinks with os.path.realpath()
    2. Verifying the resolved path is within the session sandbox

    Args:
        path: The path to resolve (can be absolute or relative)
        workspace_id: Workspace identifier
        agent_id: Agent identifier
        session_id: Session identifier

    Returns:
        The secure absolute path within the sandbox

    Raises:
        ValueError: If path is outside the session sandbox or IDs are missing
    """
    if not workspace_id or not agent_id or not session_id:
        raise ValueError("workspace_id, agent_id, and session_id are all required")

    # Ensure session directory exists: runtime/workspace_id/agent_id/session_id
    session_dir = os.path.join(WORKSPACES_DIR, workspace_id, agent_id, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Resolve the session directory to its real path (follows symlinks)
    session_dir_real = os.path.realpath(session_dir)

    # Resolve absolute path
    if os.path.isabs(path):
        # Treat absolute paths as relative to the session root if they start with /
        rel_path = path.lstrip(os.sep)
        final_path = os.path.join(session_dir, rel_path)
    else:
        final_path = os.path.join(session_dir, path)

    # Resolve to real path (follows symlinks) - this prevents symlink attacks
    final_path_real = os.path.realpath(final_path)

    # Verify path is within session_dir using the real paths
    try:
        common_prefix = os.path.commonpath([final_path_real, session_dir_real])
    except ValueError as err:
        # Different drives on Windows or other path incompatibility
        raise ValueError(f"Access denied: Path '{path}' is outside the session sandbox.") from err

    if common_prefix != session_dir_real:
        raise ValueError(f"Access denied: Path '{path}' is outside the session sandbox.")

    return final_path_real
