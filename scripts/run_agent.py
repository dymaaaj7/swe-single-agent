#!/usr/bin/env python3
"""
Run SWE-agent programmatically on a local test repository.

This script demonstrates how to use SWE-agent without the terminal/CLI.
It creates all configuration objects in Python and runs the agent directly.

Usage:
    python scripts/run_agent.py

Requirements:
    - SWE-agent installed in your virtual environment
    - Model API keys set in .env file
    - test_repo/ directory with the buggy code
"""

import sys
from pathlib import Path

# Add the parent directory to Python path so we can import sweagent
# This assumes you're running from the project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from swerex.deployment.config import LocalDeploymentConfig

from sweagent.agent.agents import AgentConfig, DefaultAgentConfig, TemplateConfig
from sweagent.agent.models import ModelConfig
from sweagent.agent.problem_statement import TextProblemStatement
from sweagent.environment.swe_env import EnvironmentConfig
from sweagent.run.run_single import RunSingle, RunSingleActionConfig, RunSingleConfig
from sweagent.tools.tools import ToolConfig

# =============================================================================
# CONFIGURATION - Modify these values for your use case
# =============================================================================

# Paths
TEST_REPO_NAME = "test_repo"  # Name of the test repo directory
TEST_REPO_PATH = Path(__file__).parent.parent / TEST_REPO_NAME  # Full path to test_repo
OUTPUT_DIR = Path("./output")  # Where to save results

# The problem statement - describe the bug to fix
PROBLEM_STATEMENT = """The divide() function in calculator.py crashes when dividing by zero.

Current behavior:
- Calling divide(10, 0) raises a ZeroDivisionError

Expected behavior:
- The function should check if the divisor (b) is zero
- If it is zero, raise a ValueError with the exact message: "Cannot divide by zero!"
- Otherwise, perform the division as normal

Please fix the divide() function to handle this edge case properly.
"""

# Model configuration - uses GLM model from your default_with_env.yaml
MODEL_CONFIG = ModelConfig(
    name="openai/glm-4.7",  # Your GLM model
    per_instance_cost_limit=0,  # Disable cost tracking (LiteLLM doesn't know glm-4.7 pricing)
    total_cost_limit=0,
    per_instance_call_limit=100,  # Limit number of calls instead
    max_input_tokens=128000,
    max_output_tokens=8192,
    temperature=0.0,
    top_p=1.0,
)

# Template configuration - copied from default_with_env.yaml
SYSTEM_TEMPLATE = """You are a helpful assistant that can interact with a computer to solve tasks.

You must format your response exactly as follows:
DISCUSSION
Discuss here with yourself about what you're planning and what you're going to do in this step.

```
command(s) that you're going to run
```

Always include the DISCUSSION header followed by your reasoning, then a blank line, then your command(s) in a code block.
"""

INSTANCE_TEMPLATE = """<uploaded_files>
{{working_dir}}
</uploaded_files>
I've uploaded a python code repository in the directory {{working_dir}}. Consider the following PR description:

<pr_description>
{{problem_statement}}
</pr_description>

Can you help me implement the necessary changes to the repository so that the requirements specified in the <pr_description> are met?
I've already taken care of all changes to any of the test files described in the <pr_description>. This means you DON'T have to modify the testing logic or any of the tests in any way!
Your task is to make the minimal changes to non-tests files in the {{working_dir}} directory to ensure the <pr_description> is satisfied.
Follow these steps to resolve the issue:
1. As a first step, it might be a good idea to find and read code relevant to the <pr_description>
2. Create a script to reproduce the error and execute it with `python <filename.py>` using the bash tool, to confirm the error
3. Edit the sourcecode of the repo to resolve the issue
4. Rerun your reproduce script and confirm that the error is fixed!
5. Think about edgecases and make sure your fix handles them as well
Your thinking should be thorough and so it's fine if it's very long.
"""

NEXT_STEP_TEMPLATE = """OBSERVATION:
{{observation}}
"""

NEXT_STEP_NO_OUTPUT_TEMPLATE = "Your command ran successfully and did not produce any output."


# =============================================================================
# MAIN SCRIPT
# =============================================================================


def create_agent_config() -> AgentConfig:
    """Create the agent configuration with templates and tools."""

    # Template configuration
    templates = TemplateConfig(
        system_template=SYSTEM_TEMPLATE,
        instance_template=INSTANCE_TEMPLATE,
        next_step_template=NEXT_STEP_TEMPLATE,
        next_step_no_output_template=NEXT_STEP_NO_OUTPUT_TEMPLATE,
        max_observation_length=100_000,
    )

    # Tool configuration - enable bash and file editing tools
    # Use a local tools directory for local deployment (not /root/tools which requires root)
    tools = ToolConfig(
        env_variables={
            "PAGER": "cat",
            "MANPAGER": "cat",
            "LESS": "-R",
            "PIP_PROGRESS_BAR": "off",
            "TQDM_DISABLE": "1",
            "GIT_PAGER": "cat",
        },
        enable_bash_tool=True,
        parse_function={"type": "thought_action"},  # Use thought_action parsing
        tools_dir="/tmp/swe-agent-tools",  # Local writable directory
        bundles=[
            {"path": "tools/registry"},
            {"path": "tools/edit_anthropic"},
            {"path": "tools/submit"},
        ],
        registry_variables={
            "USE_FILEMAP": "true",
            "SUBMIT_REVIEW_MESSAGES": [
                "Thank you for your work on this issue. Please carefully follow the steps below to help review your changes.\n"
                "1. If you made any changes to your code after running the reproduction script, please run the reproduction script again.\n"
                "2. Remove your reproduction script (if you haven't done so already).\n"
                "3. If you have modified any TEST files, please revert them.\n"
                "4. Run the submit command again to confirm."
            ],
        },
    )

    # Create the full agent config
    return DefaultAgentConfig(
        name="test_agent",
        templates=templates,
        tools=tools,
        model=MODEL_CONFIG,
        max_requeries=3,
    )


def create_environment_config() -> EnvironmentConfig:
    """Create the environment configuration for local execution."""

    # Use local deployment (runs in subprocess, no Docker needed)
    deployment = LocalDeploymentConfig()

    # For local execution, we don't use the repo config (it tries to copy to /test_repo)
    # Instead, we use post_startup_commands to navigate to the repo directory
    repo_path = Path(TEST_REPO_PATH).resolve()

    return EnvironmentConfig(
        deployment=deployment,
        repo=None,  # No repo copying - we navigate directly to it
        post_startup_commands=[
            f"cd {repo_path}",
            "export ROOT=$(pwd -P)",
        ],
        name="test_env",
    )


def main():
    """Main entry point - configure and run the agent."""

    print("=" * 70)
    print("SWE-agent Programmatic Runner")
    print("=" * 70)
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create the problem statement
    print("Creating problem statement...")
    problem_statement = TextProblemStatement(
        text=PROBLEM_STATEMENT,
        id="test_divide_by_zero",  # Unique ID for this issue
    )
    print(f"  Problem ID: {problem_statement.id}")
    print()

    # Create configurations
    print("Creating configurations...")
    env_config = create_environment_config()
    agent_config = create_agent_config()
    print("  Environment config: OK")
    print("  Agent config: OK")
    print()

    # Create the main run configuration
    print("Building RunSingle configuration...")
    config = RunSingleConfig(
        env=env_config,
        agent=agent_config,
        problem_statement=problem_statement,
        output_dir=OUTPUT_DIR,
        actions=RunSingleActionConfig(
            apply_patch_locally=True,  # Apply the fix directly to the local files
            open_pr=False,
        ),
    )
    print("  Configuration complete!")
    print()

    # Create and run the agent
    print("Initializing agent...")
    try:
        runner = RunSingle.from_config(config)
        print("  Agent initialized successfully!")
        print()

        print("Running agent (this may take a while)...")
        print("-" * 70)
        runner.run()
        print("-" * 70)
        print()

        print("Agent completed successfully!")
        print(f"Results saved to: {OUTPUT_DIR / problem_statement.id}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
