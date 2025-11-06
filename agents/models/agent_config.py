"""Configuration-based agent definitions."""

from typing import Dict, Any
from pathlib import Path
import json

from .base_agent import BaseAgent, AgentFactory


class AgentConfig:
    """Class for managing agent configurations."""

    def __init__(self, config_path: str = None):
        """
        Initialize agent configuration.

        Args:
            config_path: Path to configuration file (JSON or YAML)
        """
        self.config_path = config_path
        self.agents_config = {}

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str):
        """Load agent configurations from file."""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                self.agents_config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON format in configuration file") from e
        except Exception as e:
            raise ValueError("Error reading configuration file") from e

    def get_agent_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""

        if name not in self.agents_config:
            raise KeyError(f"Agent configuration '{name}' not found")
        return self.agents_config[name]

    def create_agent(self, name: str) -> BaseAgent:
        """Create an agent from configuration."""

        config = self.get_agent_config(name)
        return AgentFactory.create_agent_from_config(config)

    def create_all_agents(self) -> Dict[str, BaseAgent]:
        """Create all agents from configuration."""

        agents = {}
        for name in self.agents_config:
            agents[name] = self.create_agent(name)
        return agents
