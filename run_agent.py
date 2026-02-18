#!/usr/bin/env python3
"""
Python script to run SWE-agent on a single instance.

This is equivalent to running:
    sweagent run \
        --config config/custom.yaml \
        --problem_statement.path test_repo/problem.md \
        --env.repo.path test_repo

Usage:
    python run_sweagent.py

You can modify the configuration variables below to customize the run.
"""

from pathlib import Path

from sweagent.agent.agents import DefaultAgentConfig
from sweagent.agent.problem_statement import TextProblemStatement
from sweagent.environment.swe_env import EnvironmentConfig
from sweagent.run.run_single import RunSingle, RunSingleConfig
from sweagent.utils.config import load_environment_variables


def main():
    # ============================================================
    # CONFIGURATION - Modify these values as needed
    # ============================================================

    # Path to the config file (YAML)
    # Use the directory where this script is located as the base
    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / "config" / "custom.yaml"

    # Path to the problem statement file (markdown)
    # problem_statement_path = Path.home() / "Documents" / "cvetko" / "problem.md"

    # Path to the repository
    repo_path = Path.home() / "Documents" / "cvetko" / "test-project-for-agents"

    # Output directory for trajectories and results
    output_dir = script_dir / "trajectories"

    # Optional: Set a specific model name (overrides config file)
    # model_name = "gpt-4o"  # Uncomment to override

    # ============================================================
    # LOAD CONFIGURATION
    # ============================================================

    # Load environment variables from .env file if present
    load_environment_variables()

    # Load the base configuration from YAML file
    import yaml

    config_data = yaml.safe_load(config_path.read_text())

    # Create agent config from the YAML data
    agent_config = DefaultAgentConfig.model_validate(config_data.get("agent", {}))

    # Create environment config
    env_config = EnvironmentConfig(
        repo={"path": str(repo_path)},  # type: ignore
    )

    # Read the problem statement from file
    problem_text = """(venv) mita@china-shit:~/Documents/cvetko/test-project-for-agents$ python main.py
    Traceback (most recent call last):
    File "/home/mita/Documents/cvetko/test-project-for-agents/main.py", line 25, in <module>
        main()
    File "/home/mita/Documents/cvetko/test-project-for-agents/main.py", line 20, in main
        result = greet_user(user_name, user_age)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/home/mita/Documents/cvetko/test-project-for-agents/main.py", line 10, in greet_user
        message = "Hello, " + name + "! You were born in " + birth_year
                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^~~~~~~~~~~~
    TypeError: can only concatenate str (not "int") to str
    This is the error that I get. Can you fix it please?"""
    # problem_text = problem_statement_path.read_text()
    problem_statement = TextProblemStatement(text=problem_text)

    # ============================================================
    # CREATE AND RUN
    # ============================================================

    # Build the full configuration
    config = RunSingleConfig(
        env=env_config,
        agent=agent_config,
        problem_statement=problem_statement,  # type: ignore
        output_dir=output_dir,
    )

    # Run the agent
    print("Running SWE-agent with:")
    print(f"  Config: {config_path}")
    print(f"  Problem: {problem_statement}")
    print(f"  Repo: {repo_path}")
    print(f"  Output: {output_dir}")
    print()

    RunSingle.from_config(config).run()

    print("\nDone!")


if __name__ == "__main__":
    main()
