# SWE-agent Programmatic Test Scripts

This directory contains scripts demonstrating how to use SWE-agent programmatically without the terminal/CLI.

## Files

### `run_agent.py`
Full-featured example with detailed configuration, comments, and all options explained.

**Usage:**
```bash
python scripts/run_agent.py
```

**Features:**
- Complete configuration setup
- Detailed logging/output
- All template and tool configurations
- Error handling

### `run_agent_simple.py`
Minimal example showing the essential code needed to run SWE-agent.

**Usage:**
```bash
python scripts/run_agent_simple.py
```

**Features:**
- Concise code
- Minimal configuration
- Same end result

## How It Works

Both scripts follow the same pattern:

1. **Create Configuration Objects**
   - `EnvironmentConfig` - Sets up local deployment and repo
   - `AgentConfig` - Configures model, templates, and tools
   - `ProblemStatement` - Defines the issue to fix
   - `RunSingleConfig` - Combines everything

2. **Instantiate the Runner**
   ```python
   runner = RunSingle.from_config(config)
   ```

3. **Run the Agent**
   ```python
   runner.run()
   ```

## Configuration Details

### Model Configuration
The scripts use your GLM model settings from `default_with_env.yaml`:
- Model: `openai/glm-4.7`
- Cost tracking disabled (LiteLLM doesn't know GLM pricing)
- Call limit: 50-100 per instance

### Environment
- **Deployment**: `LocalDeploymentConfig` - runs in subprocess, no Docker needed
- **Repo**: Set to `None` with `post_startup_commands` to navigate to the repo directory (avoids permission issues)

### Tools Enabled
- `tools/registry` - File navigation and state management
- `tools/edit_anthropic` - File editing capabilities
- Bash tool - Execute commands

### Output
Results are saved to `./output/<problem_id>/`:
- `config.yaml` - The configuration used
- `*.log` - Log files at different levels
- `model_predictions.json` - Agent predictions
- Applied directly to `test_repo/` if `apply_patch_locally=True`

## Customization

### Change the Problem
Modify the `PROBLEM_STATEMENT` variable in the scripts:

```python
problem_statement = TextProblemStatement(
    id="my_issue",
    text="Describe the bug here..."
)
```

### Use a Different Model
Change the model configuration:

```python
model=ModelConfig(
    name="anthropic/claude-3-opus",  # or gpt-4o, etc.
    per_instance_call_limit=100,
)
```

### Different Repository
For local execution without Docker, set `repo=None` and use `post_startup_commands`:

```python
from pathlib import Path

repo_path = Path("/path/to/repo").resolve()

env_config = EnvironmentConfig(
    deployment=LocalDeploymentConfig(),
    repo=None,  # Don't copy repo
    post_startup_commands=[
        f"cd {repo_path}",
        "export ROOT=$(pwd -P)",
    ],
)
```

Note: This approach avoids permission issues that occur when trying to copy to `/repo_name`.

## Troubleshooting

### "No module named 'sweagent'"
Make sure you're running from the project root and the virtual environment is activated:
```bash
cd /home/mita/source/swe-single
source venv/bin/activate
python scripts/run_agent.py
```

### API Key Errors
Ensure your `.env` file has the required keys:
```bash
OPENAI_API_KEY=your-key-here
OPENAI_MODEL_NAME=openai/glm-4.7
OPENAI_BASE_URL=your-endpoint-url
```

### Tool Errors
If tools fail to load, check that the `tools/` directory exists and contains:
- `registry/`
- `edit_anthropic/`
- `review_on_submit_m/`

## Next Steps

1. Modify `test_repo/calculator.py` with different bugs
2. Create new problem statements
3. Extend the scripts to batch-process multiple issues
4. Add custom hooks for monitoring progress
