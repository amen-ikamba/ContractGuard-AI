"""Agent module for ContractGuard AI"""

from .agent_config import get_agent_config
from .orchestrator import ContractGuardAgent

__all__ = ['get_agent_config', 'ContractGuardAgent']