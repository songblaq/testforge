"""SSH connector -- execute commands on remote hosts."""

from __future__ import annotations

from typing import Any

from testforge.execution.connectors.base import BaseConnector


class SshConnector(BaseConnector):
    """Execute tests on remote hosts via SSH.

    Note: This is a placeholder.  A real implementation would use
    ``paramiko`` or ``asyncssh``.
    """

    def __init__(self, host: str, user: str = "", port: int = 22) -> None:
        self.host = host
        self.user = user
        self.port = port

    def connect(self) -> None:
        """Establish SSH connection."""
        # Placeholder: would use paramiko/asyncssh here
        raise NotImplementedError("SSH connector is not yet implemented")

    def execute(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a remote command."""
        raise NotImplementedError("SSH connector is not yet implemented")

    def disconnect(self) -> None:
        """Close SSH connection."""
        raise NotImplementedError("SSH connector is not yet implemented")
