"""Configuration-based agent definitions."""

import json
import logging
from typing import Dict, Any
from pathlib import Path

from .base_agent import BaseAgent, AgentFactory

logger = logging.getLogger(__name__)


class AgentConfig:
    """Class for managing agent configurations."""

    def __init__(self, config_path: str = None):
        """
        Initialize agent configuration.

        Args:
            config_path: Path to configuration file (JSON or YAML)
        """
        logger.info("Initializing AgentConfig with path: %s", config_path)
        self.config_path = config_path
        self.agents_config = {}

        if config_path:
            self.load_config(config_path)

    def load_config(self, config_path: str):
        """Load agent configurations from file."""
        logger.info("Loading configuration from: %s", config_path)
        config_file = Path(config_path)

        if not config_file.exists():
            logger.error("Configuration file not found: %s", config_path)
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                self.agents_config = json.load(f)
            logger.info(
                "Successfully loaded %d agent configurations", len(self.agents_config)
            )
            logger.debug("Agent names: %s", list(self.agents_config.keys()))
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON format in configuration file: %s", str(e))
            raise ValueError("Invalid JSON format in configuration file") from e
        except Exception as e:
            logger.error("Error reading configuration file: %s", str(e), exc_info=True)
            raise ValueError("Error reading configuration file") from e

    def get_agent_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent."""
        logger.debug("Getting configuration for agent: %s", name)

        if name not in self.agents_config:
            logger.error("Agent configuration '%s' not found", name)
            raise KeyError(f"Agent configuration '{name}' not found")

        logger.debug("Found configuration for agent: %s", name)
        return self.agents_config[name]

    def create_agent(self, name: str) -> BaseAgent:
        """Create an agent from configuration."""
        logger.info("Creating agent: %s", name)

        try:
            config = self.get_agent_config(name)
            agent = AgentFactory.create_agent_from_config(config)
            logger.info("Successfully created agent: %s", name)
            return agent
        except Exception as e:
            logger.error("Failed to create agent '%s': %s", name, str(e), exc_info=True)
            raise

    def create_all_agents(self) -> Dict[str, BaseAgent]:
        """Create all agents from configuration."""
        logger.info(
            "Creating all agents from configuration (%d total)", len(self.agents_config)
        )

        agents = {}
        for name in self.agents_config:
            agents[name] = self.create_agent(name)

        logger.info("Successfully created all %d agents", len(agents))
        return agents
