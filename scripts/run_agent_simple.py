#!/usr/bin/env python3
"""
Simplified version of run_agent.py - Minimal example of programmatic SWE-agent usage.

This is a more concise version that demonstrates the core API without all the configuration options.
"""

import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sweagent.run.run_single import RunSingle, RunSingleConfig, RunSingleActionConfig
from sweagent.environment.swe_env import EnvironmentConfig
from sweagent.agent.agents import DefaultAgentConfig
from sweagent.agent.problem_statement import TextProblemStatement
from sweagent.agent.models import ModelConfig
from sweagent.tools.tools import ToolConfig
from sweagent.utils.config import load_environment_variables
from swerex.deployment.config import LocalDeploymentConfig


def main():
    """Run SWE-agent with minimal configuration."""

    # Load environment variables from .env file
    load_environment_variables(Path(".env"))

    # Get test repo absolute path
    test_repo_path = (Path(__file__).parent.parent / "test_repo").resolve()

    # Define the problem
    problem = TextProblemStatement(
        id="divide_bug",
        text="""Fix the divide() function in calculator.py to handle division by zero.
The function should raise ValueError("Cannot divide by zero!") when b is 0.""",
    )

    # Create minimal agent configuration
    agent_config = DefaultAgentConfig(
        model=ModelConfig(
            name="openai/glm-4.7",
            per_instance_cost_limit=0,
            per_instance_call_limit=50,
        ),
        tools=ToolConfig(
            enable_bash_tool=True,
            parse_function={"type": "thought_action"},
            bundles=[
                {"path": "tools/registry"},
                {"path": "tools/edit_anthropic"},
            ],
            registry_variables={"USE_FILEMAP": "true"},
        ),
    )

    # Create environment configuration
    # For local execution without Docker, use repo=None and navigate via post_startup_commands
    env_config = EnvironmentConfig(
        deployment=LocalDeploymentConfig(),
        repo=None,  # No repo copying - we navigate directly to it
        post_startup_commands=[
            f"cd {test_repo_path}",
            "export ROOT=$(pwd -P)",
        ],
    )

    # Build and run
    config = RunSingleConfig(
        env=env_config,
        agent=agent_config,
        problem_statement=problem,
        output_dir=Path("./output"),
        actions=RunSingleActionConfig(apply_patch_locally=True),
    )

    print("Starting SWE-agent...")
    RunSingle.from_config(config).run()
    print("Done! Check ./output/divide_bug/ for results.")


if __name__ == "__main__":
    main()
