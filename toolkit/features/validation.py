"""Validation utilities for environments, components, and dependencies."""

import os
from pathlib import Path

import typer

from toolkit.config.constants import DEFAULT_CONFIG, MESSAGES, PATH_STRUCTURES
from toolkit.config.settings import EnvironmentConfig, settings
from toolkit.core.logging import logger


def validate_environment_config(env: str) -> EnvironmentConfig:
    """
    Validate environment and return config.

    Args:
        env: Environment name (dev, staging, prod)

    Returns:
        EnvironmentConfig object

    Raises:
        typer.Exit: If environment is invalid
    """
    try:
        env_config = settings.get_environment(env)
        logger.info(f"Target environment: {env_config.description}")
        return env_config
    except ValueError:
        valid_envs = list(settings.environments.keys()) or DEFAULT_CONFIG.VALID_ENVIRONMENTS
        logger.error(MESSAGES.ERROR_INVALID_ENVIRONMENT.format(env, ", ".join(valid_envs)))
        raise typer.Exit(1) from None


def validate_environment(env: str | None = None) -> str:
    """Validate environment parameter (legacy function)."""
    environment = env or os.getenv("ENVIRONMENT") or DEFAULT_CONFIG.DEFAULT_ENVIRONMENT
    valid_envs = list(settings.environments.keys()) or DEFAULT_CONFIG.VALID_ENVIRONMENTS

    if environment and environment not in valid_envs:
        raise ValueError(MESSAGES.ERROR_INVALID_ENVIRONMENT.format(environment, ", ".join(valid_envs)))

    # Return validated environment or default
    return environment if environment in valid_envs else DEFAULT_CONFIG.DEFAULT_ENVIRONMENT


def confirm_dangerous_operation(env_config: EnvironmentConfig, operation: str) -> None:
    """
    Ask for confirmation on production/staging operations.

    Args:
        env_config: Environment configuration
        operation: Operation description (e.g., "Apply configuration")

    Raises:
        typer.Exit: If user declines confirmation
    """
    if env_config.requires_confirmation:
        prompt = f"⚠️  {operation} on {env_config.name.upper()}. Continue?"
        if not logger.confirm(prompt, default=False):
            logger.info(f"{operation} cancelled")
            raise typer.Exit(0) from None


def find_component_directory(component_name: str) -> Path | None:
    """
    Find the directory for a given component name.

    Searches in:
    1. Apps directory (infra/stacks/apps/)
    2. Services directory (infra/stacks/services/*)
    3. Edge directory (infra/stacks/edge/)

    Args:
        component_name: Name of the component

    Returns:
        Path to component directory, or None if not found
    """
    # Check apps
    app_dir = settings.project_root / PATH_STRUCTURES.INFRA_STACKS_APPS / component_name
    if app_dir.exists():
        return app_dir

    # Validate Services
    services_base = settings.project_root / PATH_STRUCTURES.INFRA_STACKS_SERVICES
    if services_base.exists():
        for category_dir in services_base.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith("."):
                service_path = category_dir / component_name
                if service_path.exists():
                    return service_path

    # Check edge services
    edge_path = settings.project_root / PATH_STRUCTURES.EDGE_DIR / component_name
    if edge_path.exists():
        return edge_path

    return None


# =============================================================================
# Dependency Validation
# =============================================================================
