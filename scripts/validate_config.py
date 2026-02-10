#!/usr/bin/env python3
"""
Validate the SWE-agent configuration without running the agent.
This tests that all imports work and configurations are valid.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from swerex.deployment.config import LocalDeploymentConfig

from sweagent.agent.agents import DefaultAgentConfig
from sweagent.agent.models import ModelConfig
from sweagent.agent.problem_statement import TextProblemStatement
from sweagent.environment.swe_env import EnvironmentConfig
from sweagent.run.run_single import RunSingleActionConfig, RunSingleConfig
from sweagent.tools.tools import ToolConfig


def main():
    print("Validating SWE-agent configuration...")
    print()

    # Test 1: Problem Statement
    print("1. Creating problem statement...")
    problem = TextProblemStatement(
        id="test_validation",
        text="Test problem statement",
    )
    print(f"   ✓ Problem ID: {problem.id}")
    print()

    # Test 2: Model Config
    print("2. Creating model config...")
    model = ModelConfig(
        name="openai/glm-4.7",
        per_instance_cost_limit=0,
        per_instance_call_limit=100,
    )
    print(f"   ✓ Model: {model.name}")
    print()

    # Test 3: Tool Config
    print("3. Creating tool config...")
    tools = ToolConfig(
        enable_bash_tool=True,
        parse_function={"type": "thought_action"},
        bundles=[
            {"path": "tools/registry"},
            {"path": "tools/edit_anthropic"},
        ],
    )
    print(f"   ✓ Bash tool: {tools.enable_bash_tool}")
    print()

    # Test 4: Agent Config
    print("4. Creating agent config...")
    agent_config = DefaultAgentConfig(
        model=model,
        tools=tools,
    )
    print(f"   ✓ Agent name: {agent_config.name}")
    print()

    # Test 5: Environment Config
    print("5. Creating environment config...")
    test_repo_path = (Path(__file__).parent.parent / "test_repo").resolve()
    env_config = EnvironmentConfig(
        deployment=LocalDeploymentConfig(),
        repo=None,  # No repo copying - navigate directly via post_startup_commands
        post_startup_commands=[
            f"cd {test_repo_path}",
            "export ROOT=$(pwd -P)",
        ],
    )
    print(f"   ✓ Deployment type: {env_config.deployment.type}")
    print(f"   ✓ Repo: {env_config.repo.repo_name if env_config.repo else 'None (using post_startup_commands)'}")
    print()

    # Test 6: Actions Config
    print("6. Creating actions config...")
    actions = RunSingleActionConfig(
        apply_patch_locally=True,
        open_pr=False,
    )
    print(f"   ✓ Apply patch locally: {actions.apply_patch_locally}")
    print()

    # Test 7: Full Run Config
    print("7. Creating full run configuration...")
    config = RunSingleConfig(
        env=env_config,
        agent=agent_config,
        problem_statement=problem,
        output_dir=Path("./output"),
        actions=actions,
    )
    print(f"   ✓ Output dir: {config.output_dir}")
    print()

    print("=" * 50)
    print("All configurations validated successfully!")
    print()
    print("You can now run the agent with:")
    print("  python scripts/run_agent.py")
    print("or")
    print("  python scripts/run_agent_simple.py")


if __name__ == "__main__":
    main()
