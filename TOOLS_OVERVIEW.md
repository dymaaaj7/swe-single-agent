# SWE-agent Tools Overview

This document provides a comprehensive explanation of the tools system in SWE-agent, including what they are, how they work, and how they're used.

## Table of Contents

1. [What Are Tools?](#what-are-tools)
2. [Tool Architecture](#tool-architecture)
3. [Tool Bundles](#tool-bundles)
4. [How Tools Are Used](#how-tools-are-used)
5. [Tool Execution Flow](#tool-execution-flow)
6. [Configuration Examples](#configuration-examples)
7. [Do You Need All Tools?](#do-you-need-all-tools)
8. [Creating Custom Tools](#creating-custom-tools)

---

## What Are Tools?

In SWE-agent, **tools** are executable commands that the AI agent can invoke to interact with the environment. They provide structured ways to:

- **View and edit files** (reading, writing, modifying code)
- **Search the codebase** (finding files, searching text)
- **Navigate the environment** (change directories, list files)
- **Submit solutions** (finalize and submit changes)
- **Manage state** (persist information between tool calls)

Tools are organized into **bundles** - self-contained directories that include:
- The executable scripts
- Configuration defining the tool's interface
- Optional installation/setup scripts
- Optional shared libraries

---

## Tool Architecture

### Overview

The tool system is a layered architecture that bridges the gap between LLM outputs and actual shell commands executed in an environment:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LLM Output                                                             │
│  "Use str_replace_editor to view main.py"                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Parsing Layer (parsing.py)                                             │
│  Extract command name and arguments from LLM output                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Command Layer (commands.py)                                            │
│  Validate arguments, format command string                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Handler Layer (tools.py)                                               │
│  Block check → Multiline handling → Execute in environment              │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  Bundle Layer (bundle.py)                                               │
│  Tool scripts installed in /root/tools/                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### Core Components

The tool system consists of several key components in `sweagent/tools/`:

#### 1. `Bundle` and `BundleConfig` (`sweagent/tools/bundle.py`)

**Purpose**: Represents a tool bundle directory and manages loading tool definitions from `config.yaml`.

```python
class Bundle(BaseModel):
    path: Path                    # Absolute path to the tool bundle directory
    hidden_tools: list[str]       # Tools to hide from the agent (internal use)
    _config: BundleConfig         # Private: Parsed config.yaml contents
```

```python
class BundleConfig(BaseModel):
    tools: dict[str, dict]        # Raw tool definitions from config.yaml
    state_command: str | None     # Optional command to run after each action
```

**Key Methods:**

| Method | Purpose |
|--------|---------|
| `validate_tools()` | Validates bundle path exists, parses config.yaml |
| `state_command` | Returns the state command if defined |
| `commands` | Returns list of `Command` objects from the bundle |

**Example Flow:**
```python
# 1. Bundle is created from config
bundle = Bundle(path=Path("tools/edit_anthropic"))

# 2. Validator checks:
#    - Path exists?
#    - config.yaml exists?
#    - hidden_tools are valid?

# 3. Commands property parses config.yaml:
#    config.tools = {"str_replace_editor": {...}}
#    → Returns [Command(name="str_replace_editor", ...)]
```

---

#### 2. `Command` and `Argument` (`sweagent/tools/commands.py`)

**Purpose**: Defines the interface for a single tool command that the LLM can invoke.

```python
class Command(BaseModel):
    name: str                     # Command name (e.g., "str_replace_editor")
    docstring: str | None         # Description shown to the AI
    signature: str | None         # Custom calling syntax
    end_name: str | None          # Multi-line terminator (e.g., "EOF")
    arguments: list[Argument]     # List of accepted arguments
```

```python
class Argument(BaseModel):
    name: str                     # Argument name (must match [a-zA-Z_][a-zA-Z0-9_-]*)
    type: str                     # JSON schema type (string, integer, array, etc.)
    description: str              # Human-readable description for LLM
    required: bool                # Whether LLM must provide this
    enum: list[str] | None        # Allowed values (optional)
    argument_format: str          # How to format in command (default: "{{value}}")
    items: dict | None            # For arrays: defines item schema
```

**Key Properties:**

| Property | Description |
|----------|-------------|
| `invoke_format` | Generated format string for building the actual command |
| `get_function_calling_tool()` | Converts to OpenAI function calling schema |

**Signature Parsing:**

The `signature` field in config.yaml defines how the command is called:

```yaml
# Simple signature
signature: "filemap <file_path>"
# → invoke_format: "filemap {file_path}"

# Optional arguments
signature: "find_file <file_name> [<dir>]"
# → invoke_format: "find_file {file_name} {dir}"

# Named flags
signature: "str_replace_editor <command> <path> [--old_str=<old_str>]"
# → Uses argument_format from config
```

**Validation:**

The `Command` class validates:
- Required arguments come before optional ones
- No duplicate argument names
- Argument names match the pattern `[a-zA-Z_][a-zA-Z0-9_-]*`
- All arguments appear in the signature

---

#### 3. `ToolConfig` (`sweagent/tools/tools.py`)

**Purpose**: Top-level configuration that defines which tools are available and how they behave.

```python
class ToolConfig(BaseModel):
    # Bundles
    bundles: list[Bundle]                    # Tool bundles to load
    tools_dir: str = "/root/tools"           # Installation directory
    
    # Core tools
    enable_bash_tool: bool = True            # Include bash command?
    submit_command: str = "submit"           # Which command is "submit"
    
    # Parsing
    parse_function: ParseFunction            # How to parse LLM output
    
    # Environment
    env_variables: dict[str, Any]            # Env vars to set (PAGER=cat, etc.)
    registry_variables: dict[str, Any]       # Initial registry values
    propagate_env_variables: list[str]       # Env vars to pass from host
    
    # Command filtering
    filter: ToolFilterConfig                 # Blocklist for dangerous commands
    
    # Timeouts
    execution_timeout: int = 30              # Per-command timeout
    total_execution_timeout: int = 1800      # Total agent timeout
    install_timeout: int = 300               # Tool installation timeout
```

**Cached Properties:**

| Property | Computes |
|----------|----------|
| `use_function_calling` | Whether parse_function is FunctionCallingParser |
| `state_commands` | List of state commands from all bundles |
| `commands` | Combined list of all available commands (from bundles + bash) |
| `tools` | OpenAI function calling schema for all commands |

**Important Checks:**

```python
# Duplicate tool detection
for bundle in self.bundles:
    for command in bundle.commands:
        if command.name in tool_sources:
            raise ValueError(f"Tool '{command.name}' defined multiple times!")
```

---

#### 4. `ToolHandler` (`sweagent/tools/tools.py`)

**Purpose**: The main runtime class that manages tool execution. This is the bridge between the configuration and actual command execution.

```python
class ToolHandler:
    def __init__(self, tools: ToolConfig):
        self.config = tools.model_copy(deep=True)  # Deep copy to avoid shared state
        self._reset_commands = []                   # Commands to run on reset
        self._command_patterns = self._get_command_patterns()
        self.mock_state = None                      # For testing
```

**Responsibilities:**

| Area | Methods | Description |
|------|---------|-------------|
| **Installation** | `install()`, `_install_commands()`, `_upload_bundles()` | Upload tools to environment, run install.sh |
| **Reset** | `reset()` | Set up tools for each episode (env vars, registry) |
| **Blocking** | `should_block_action()` | Prevent dangerous commands (vim, nano, etc.) |
| **State** | `get_state()`, `_get_state()` | Run state commands, read state.json |
| **Parsing** | `parse_actions()` | Convert LLM output to (thought, action) tuple |
| **Multiline** | `guard_multiline_input()` | Handle heredoc-style multi-line commands |

**Installation Flow:**

```python
def install(self, env: SWEEnv):
    self._install_commands(env)  # Upload and install
    self.reset(env)              # Set up for first use

def _install_commands(self, env: SWEEnv):
    # 1. Upload all bundles to /root/tools/
    asyncio.run(self._upload_bundles(env))
    
    # 2. For each bundle:
    for bundle in self.config.bundles:
        cmds = [
            f"export PATH={tools_dir}/{bundle.path.name}/bin:$PATH",
            f"chmod +x {tools_dir}/{bundle.path.name}/bin/*",
        ]
        # Run install.sh if present
        if (bundle.path / "install.sh").exists():
            cmds.append(f"cd {tools_dir}/{bundle.path.name} && source install.sh")
        env.communicate(" && ".join(cmds))
    
    # 3. Verify all commands are available
    asyncio.run(self._check_available_commands(env, ...))
```

**State Retrieval Flow:**

```python
def get_state(self, env: SWEEnv) -> dict[str, str]:
    # 1. Run all state commands from bundles
    for state_command in self.config.state_commands:
        env.communicate(state_command, check="warn")
    
    # 2. Read the combined state from state.json
    return self._get_state(env)

def _get_state(self, env: SWEEnv) -> dict[str, str]:
    state_str = env.read_file(f"{tools_dir}/state.json")
    return json.loads(state_str)
```

**Command Blocking:**

```python
def should_block_action(self, action: str) -> bool:
    # Block by prefix (e.g., "vim", "nano")
    if any(action.startswith(f) for f in self.config.filter.blocklist):
        return True
    
    # Block exact matches (e.g., "python", "bash")
    if action in self.config.filter.blocklist_standalone:
        return True
    
    # Block unless regex matches (e.g., radare2 needs -c flag)
    name = action.split()[0]
    if name in self.config.filter.block_unless_regex:
        if not re.search(self.config.filter.block_unless_regex[name], action):
            return True
    
    return False
```

---

#### 5. Parsers (`sweagent/tools/parsing.py`)

**Purpose**: Convert LLM output into executable commands. Two main implementations:

##### ThoughtActionParser

For models that output text with code blocks:

```
Let me check the file structure first.

```
str_replace_editor view /workspace/main.py
```
```

**Algorithm:**
1. Find all code block markers (```)
2. Track nesting with a stack
3. Return the last non-nested code block as the action
4. Everything else is the "thought"

```python
def __call__(self, model_response: dict, commands: list[Command], strict=False):
    code_block_pat = re.compile(r"^```(\S*)\s*\n|^```\s*$", re.MULTILINE)
    stack = []
    last_valid_block = None
    
    for match in code_block_pat.finditer(model_response["message"]):
        if stack and not match.group(1):  # Closing
            start = stack.pop()
            if not stack:  # Not nested
                last_valid_block = (start, match)
        elif match.group(1) is not None:  # Opening
            stack.append(match)
    
    if last_valid_block:
        start, end = last_valid_block
        thought = message[:start.start()] + message[end.end():]
        action = message[start.end():end.start()]
        return thought, action
```

##### FunctionCallingParser

For models that support native function calling (OpenAI, Claude):

```json
{
  "tool_calls": [{
    "function": {
      "name": "str_replace_editor",
      "arguments": {"command": "view", "path": "/workspace/main.py"}
    }
  }]
}
```

**Algorithm:**
1. Extract the single tool call from `tool_calls` array
2. Validate command exists
3. Validate all required arguments are present
4. Validate no unexpected arguments
5. Format arguments using `argument_format` from config
6. Return formatted command string

```python
def _parse_tool_call(self, tool_call: dict, commands: list[Command]):
    name = tool_call["function"]["name"]
    command = {c.name: c for c in commands}.get(name)
    
    # Validate
    if not command:
        raise FunctionCallingFormatError(f"Command '{name}' not found")
    
    values = json.loads(tool_call["function"]["arguments"])
    
    required_args = {arg.name for arg in command.arguments if arg.required}
    missing = required_args - values.keys()
    if missing:
        raise FunctionCallingFormatError(f"Missing: {missing}")
    
    # Format
    formatted_args = {
        arg.name: Template(arg.argument_format).render(value=values[arg.name])
        for arg in command.arguments if arg.name in values
    }
    
    return command.invoke_format.format(**formatted_args).strip()
```

---

#### 6. Utilities (`sweagent/tools/utils.py`)

**Purpose**: Helper functions for command handling.

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `_guard_multiline_input()` | Splits actions by multi-line commands, appends `<< 'end_name'` for heredocs |
| `_should_quote()` | Determines if an argument needs shell quoting |
| `get_signature()` | Extracts signature from bash script docstrings |
| `generate_command_docs()` | Creates formatted documentation for prompts |

**Multi-line Command Handling:**

For commands like `str_replace_editor str_replace` that take multi-line text:

```yaml
# config.yaml
arguments:
  - name: old_str
    type: string
    argument_format: "--old_str {{value}}"
  - name: new_str
    type: string
    argument_format: "--new_str {{value}}"
```

The `_guard_multiline_input()` function transforms:
```
str_replace_editor str_replace /file.py --old_str "line1
line2" --new_str "new"
```

Into:
```
str_replace_editor str_replace /file.py --old_str << 'EOF'
line1
line2
EOF
 --new_str "new"
```

This uses bash heredocs to safely pass multi-line strings.

---

### Component Interactions

Here's how all components work together during a single step:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ AGENT STEP                                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Agent calls model with prompt (includes {{command_docs}})              │
│                                                                             │
│  2. LLM responds with tool call                                            │
│     → FunctionCallingParser or ThoughtActionParser extracts it             │
│                                                                             │
│  3. ToolHandler.parse_actions() returns (thought, action)                  │
│                                                                             │
│  4. ToolHandler checks should_block_action(action)                         │
│     → Blocks if matches blocklist                                          │
│                                                                             │
│  5. ToolHandler.guard_multiline_input(action)                              │
│     → Transforms multi-line arguments to heredocs                          │
│                                                                             │
│  6. Action executed in SWEEnv (Docker container)                           │
│     → Output captured as observation                                       │
│                                                                             │
│  7. ToolHandler.get_state(env) runs state commands                         │
│     → Updates state.json                                                   │
│                                                                             │
│  8. State used to fill template variables ({{working_dir}}, etc.)          │
│                                                                             │
│  9. Observation + state go back to LLM in next prompt                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tool Bundles

There are 6 tool bundles in the `tools/` directory:

### 1. `registry/` - State Management

**Purpose**: Provides shared state management (no tools exposed to agent)

**Files:**
```
tools/registry/
├── config.yaml          # Empty tools dict (no exposed tools)
├── lib/
│   ├── __init__.py
│   └── registry.py      # EnvRegistry class for state persistence
└── bin/
    ├── _read_env        # Internal: Read registry value
    └── _write_env       # Internal: Write registry value
```

**Key Functionality:**
```python
# Other tools import this to persist state
from registry import registry

# Read a value (with fallback to environment variables)
value = registry.get("KEY", default_value="fallback")

# Write a value
registry["KEY"] = "new_value"
```

**Why it's needed**: Environment variables cannot be set in subprocesses and persist to parent shells. The registry uses a JSON file (`/root/.swe-agent-env`) to share state between tool calls.

**Essential?** ✅ **YES** - Required by other tools.

---

### 2. `edit_anthropic/` - File Editing

**Purpose**: Comprehensive file viewing and editing (adapted from Anthropic's computer use demo)

**Tool:** `str_replace_editor`

**Commands:**
| Command | Description |
|---------|-------------|
| `view` | Display file contents with line numbers |
| `create` | Create a new file |
| `str_replace` | Replace text using exact string matching |
| `insert` | Insert text at a specific line |
| `undo_edit` | Revert the last edit |

**Example Usage:**
```bash
# View a file
str_replace_editor view /path/to/file.py

# View specific lines
str_replace_editor view /path/to/file.py --view_range 10 20

# Replace text
str_replace_editor str_replace /path/to/file.py \
  --old_str "def old_function():" \
  --new_str "def new_function():"

# Create a file
str_replace_editor create /path/to/new_file.py --file_text "print('hello')"
```

**Features:**
- Truncates long outputs with a notice
- Integrates with `filemap` for Python files (when `USE_FILEMAP=true`)
- Optional flake8 linting (when `USE_LINTER=true`)
- Line number display
- Multi-line edit support

**Files:**
```
tools/edit_anthropic/
├── config.yaml              # Tool interface definition
├── install.sh               # Installs tree-sitter dependencies
└── bin/
    ├── str_replace_editor   # Main editing tool (Python script)
    └── _state_anthropic     # State command: returns current file
```

**Essential?** ⚡ **Highly Recommended** - Provides structured editing that's safer than raw bash.

---

### 3. `filemap/` - Python File Viewing

**Purpose**: Display Python files while skipping lengthy function definitions to save context tokens.

**Tool:** `filemap`

**How it works:**
1. Uses tree-sitter to parse Python files
2. Identifies function/method definitions
3. Elides (replaces with `... eliding lines X-Y ...`) functions longer than 5 lines
4. Shows line numbers for all visible content

**Example Output:**
```python
     1 import os
     2 
     3 ... eliding lines 3-15 ...
    16 
    17 def short_func():
    18     return 42
    19 
    20 ... eliding lines 20-45 ...
```

**Usage:**
```bash
filemap /path/to/file.py
```

**Integration:**
The `str_replace_editor` automatically uses `filemap` for Python files when `USE_FILEMAP=true` is set in the registry.

**Files:**
```
tools/filemap/
├── config.yaml
├── install.sh               # Installs tree-sitter
└── bin/
    └── filemap              # Python script using tree-sitter
```

**Essential?** ❌ **Optional** - Convenient but can be replaced with `cat`, `head`, `tail` bash commands.

---

### 4. `search/` - Code Search

**Purpose**: Search for files and text in the codebase.

**Tools:**

| Tool | Purpose | Example |
|------|---------|---------|
| `find_file` | Find files by name/pattern | `find_file "*.py" /src` |
| `search_dir` | Search for text in all files | `search_dir "def foo" /src` |
| `search_file` | Search for text in a specific file | `search_file "TODO" file.py` |

**Implementation:**
- Shell scripts wrapping `find` and `grep`
- Supports wildcards (`*.py`)
- Shows match counts

**Examples:**
```bash
# Find all Python test files
find_file "test_*.py" .

# Search for a function definition
search_dir "def calculate_total" .

# Search in a specific file
search_file "FIXME" /path/to/file.py
```

**Files:**
```
tools/search/
├── config.yaml
├── install.sh
└── bin/
    ├── find_file       # Bash script
    ├── search_dir      # Bash script
    └── search_file     # Bash script
```

**Essential?** ❌ **Optional** - Can be replaced with `find`, `grep`, `rg` (ripgrep) bash commands.

---

### 5. `review_on_submit_m/` - Submission with Review

**Purpose**: Multi-stage submission process with review workflow.

**Tool:** `submit`

**How it works:**
1. Agent calls `submit` when ready to finish
2. Tool generates a git patch of all changes
3. Tool displays a review message from `SUBMIT_REVIEW_MESSAGES` registry variable
4. Agent reviews the diff and confirms
5. On confirmation, outputs `<<SWE_AGENT_SUBMISSION>>` with the patch

**Features:**
- Configurable review messages (multi-stage possible)
- Shows git diff of all changes
- Forces agent to review their work before final submission
- Supports force submit with `-f` flag

**Configuration Example:**
```yaml
registry_variables:
  SUBMIT_REVIEW_MESSAGES:
    - |
      Please review your changes:
      <diff>{{diff}}</diff>
      
      Run the tests again to verify.
    - |
      Are you sure you want to submit?
      Confirm by running submit again.
```

**Files:**
```
tools/review_on_submit_m/
├── config.yaml
├── README.md
├── install.sh
└── bin/
    └── submit          # Python script
```

**Essential?** ⚡ **Recommended** - Prevents premature submissions and encourages code review.

---

### 6. `submit/` - Simple Submission

**Purpose**: Basic submission without review workflow.

**Tool:** `submit`

**Behavior:**
- Immediately outputs `<<SWE_AGENT_SUBMISSION>>` with git patch
- No review process
- Minimal implementation

**Use when:** You want a simpler workflow without the review stages.

**Files:**
```
tools/submit/
├── config.yaml
└── bin/
    └── submit
```

**Essential?** ❌ **Alternative** - Use either this OR `review_on_submit_m`, not both.

---

## How Tools Are Used

### Tool Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│  1. CONFIGURATION                                            │
│     User specifies bundles in config.yaml                   │
│     bundles:                                                │
│       - path: tools/registry                                │
│       - path: tools/edit_anthropic                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. INSTALLATION (when agent starts)                         │
│     ToolHandler.install(env)                                │
│     ├── Upload bundles to /root/tools/                      │
│     ├── Run install.sh for each bundle                      │
│     ├── Make scripts executable                             │
│     └── Verify commands are available                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. EXECUTION (each step)                                    │
│     Agent generates command → parse_actions()               │
│     ├── Check if blocked (vim, nano, etc.)                  │
│     ├── Handle multi-line commands                          │
│     └── Execute in environment                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. STATE RETRIEVAL                                          │
│     ToolHandler.get_state(env)                              │
│     ├── Run state_command from each bundle                  │
│     └── Parse state.json for template variables             │
└─────────────────────────────────────────────────────────────┘
```

### State Commands

State commands are **special commands** that run after every action to capture and persist environment state. They allow the agent to "remember" things across steps.

#### How They Work

1. **Defined in config.yaml**:
```yaml
# tools/edit_anthropic/config.yaml
state_command: "_state_anthropic"
```

2. **The script writes to `state.json`**:
```python
# tools/edit_anthropic/bin/_state_anthropic
import json
import os
from pathlib import Path

def main():
    # Read existing state
    state_path = Path("/root/tools/state.json")
    if state_path.exists():
        state = json.loads(state_path.read_text())
    else:
        state = {}
    
    # Add current working directory
    state["working_dir"] = os.getcwd()
    
    # Write back to state.json
    state_path.write_text(json.dumps(state))
```

3. **Agent retrieves state after each action**:
```python
# From sweagent/tools/tools.py ToolHandler.get_state()
for state_command in self.config.state_commands:
    env.communicate(state_command, check="warn")  # Run each state command
combined_state = self._get_state(env)  # Read state.json
```

#### Why Use State Commands?

**Problem**: Environment variables set in one command don't persist to the next because each command runs in a fresh shell.

**Solution**: State commands capture important state to a file (`state.json`), which is then:
- Read by the agent
- Used to fill template variables like `{{working_dir}}`
- Included in the next LLM prompt

#### Example: Tracking the Working Directory

```python
# In your tool script (e.g., str_replace_editor)
# After viewing a file, record it in state:
state["open_file"] = "/path/to/file.py"
state_path.write_text(json.dumps(state))
```

```python
# In _state_anthropic
# This runs after EVERY action
state["working_dir"] = os.getcwd()
```

```yaml
# In your prompt template
instance_template: |-
  Currently open file: {{open_file}}
  Working directory: {{working_dir}}
```

#### State Commands vs Registry

| Feature | State Command | Registry |
|---------|--------------|----------|
| **Purpose** | Capture env state for templates | Share data between tool calls |
| **Updated** | After every action | When tools explicitly write |
| **Used by** | Agent templates | Tool scripts themselves |
| **File** | `state.json` | `.swe-agent-env` |

- **State commands** = "What is the current state of the environment?" (for prompts)
- **Registry** = "Store this value so other tools can read it later" (for tool communication)

---

## Tool Execution Flow

This section explains exactly how tools are invoked during an agent run - from configuration to observation.

### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Agent Setup                                                    │
│  You configure tools in config.yaml:                                    │
│    tools:                                                               │
│      bundles:                                                           │
│        - path: tools/edit_anthropic   ← str_replace_editor available    │
│        - path: tools/search           ← search_dir, find_file available │
│                                                                         │
│  These get installed to /root/tools/ in the environment                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: LLM Prompt                                                     │
│  The agent sends the LLM a prompt that includes:                        │
│    - The problem to solve                                               │
│    - Available tools documentation (from config.yaml signatures)        │
│    - History of previous actions/observations                           │
│                                                                         │
│  Example prompt snippet:                                                │
│    "Available commands:                                                 │
│     - str_replace_editor <command> <path> ...                           │
│     - search_dir <search_term> [<dir>]                                  │
│     - bash <command>"                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: LLM Decides                                                    │
│  LLM thinks: "I need to see what's in main.py"                          │
│                                                                         │
│  LLM outputs (with function calling):                                   │
│    function: str_replace_editor                                         │
│    arguments: {command: "view", path: "/workspace/main.py"}             │
│                                                                         │
│  OR with thought_action parser:                                         │
│    Let me first look at the main file to understand the structure.      │
│    ```                                                                  │
│    str_replace_editor view /workspace/main.py                           │
│    ```                                                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 4: Parse & Execute                                                │
│  sweagent/tools/parsing.py extracts the command from LLM output         │
│                                                                         │
│  ToolHandler runs: /root/tools/edit_anthropic/bin/str_replace_editor    │
│                    view /workspace/main.py                              │
│                                                                         │
│  IN THE ENVIRONMENT (Docker/container):                                 │
│    - The script executes                                                │
│    - Reads /workspace/main.py                                           │
│    - Outputs file contents with line numbers                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 5: Observation Returned                                           │
│  Output from the tool is captured as "observation"                      │
│                                                                         │
│  Observation:                                                           │
│    "     1 import os                                                    │
│          2                                                              │
│          3 def main():                                                  │
│          4     print('hello')                                           │
│          5 ..."                                                         │
│                                                                         │
│  This goes back to the LLM in the next prompt                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 6: Loop Continues                                                 │
│  LLM sees the file content and decides next action:                     │
│    "I see the issue on line 4. Let me fix it."                          │
│                                                                         │
│  function: str_replace_editor                                           │
│  arguments: {                                                           │
│    command: "str_replace",                                              │
│    path: "/workspace/main.py",                                          │
│    old_str: "print('hello')",                                           │
│    new_str: "print('hello world')"                                      │
│  }                                                                      │
│                                                                         │
│  → Back to Step 4, continues until submit or exit                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### Two Ways LLM Can Call Tools

#### 1. Function Calling (Modern Models: GPT-4, Claude, etc.)

```json
{
  "function": "str_replace_editor",
  "arguments": {
    "command": "view",
    "path": "/workspace/main.py"
  }
}
```

**Configured with:**
```yaml
tools:
  parse_function:
    type: function_calling
```

#### 2. Thought + Action (Older/Simpler Models)

The LLM outputs text with a code block containing the command:

```
Let me check the main file first to understand the structure.

```
str_replace_editor view /workspace/main.py
```
```

**Configured with:**
```yaml
tools:
  parse_function:
    type: thought_action
```

### Key Points

1. **You define available tools** in the config - the LLM only knows about tools you give it
2. **LLM chooses which tool** based on the documentation in its prompt
3. **The script runs in the environment** (Docker container or local shell)
4. **LLM sees the output** and decides the next step
5. **This loops** until the task is done or `submit` is called

---

## Configuration Examples

### Minimal (bash only)
```yaml
# config/bash_only.yaml
tools:
  enable_bash_tool: true
  bundles: []  # No additional tools
```

### Standard (recommended)
```yaml
# config/default.yaml
tools:
  enable_bash_tool: true
  bundles:
    - path: tools/registry
    - path: tools/edit_anthropic
    - path: tools/review_on_submit_m
  registry_variables:
    USE_FILEMAP: "true"
    SUBMIT_REVIEW_MESSAGES:
      - "Please review your changes..."
```

### Full-featured
```yaml
# config/custom.yaml
tools:
  enable_bash_tool: true
  bundles:
    - path: tools/registry
    - path: tools/edit_anthropic
    - path: tools/filemap
    - path: tools/search
    - path: tools/review_on_submit_m
  registry_variables:
    USE_FILEMAP: "true"
    USE_LINTER: "true"
```

---

## Do You Need All Tools?

| Tool | Essential | Can Replace With | Use When |
|------|-----------|------------------|----------|
| `registry` | ✅ YES | Nothing (required) | Always needed |
| `edit_anthropic` | ⚡ Recommended | bash `sed`, `echo`, `cat` | You want structured editing |
| `filemap` | ❌ No | bash `cat`, `head`, `tail` | Working with large Python files |
| `search` | ❌ No | bash `find`, `grep`, `rg` | You want convenient search |
| `review_on_submit_m` | ⚡ Recommended | `submit` (simpler) | You want review workflow |
| `submit` | ❌ No | `review_on_submit_m` | You want simple submission |

### Decision Tree

```
Do you need file editing?
├── NO → Use bash_only.yaml (just bash tool)
└── YES → Use edit_anthropic
    │
    ├── Working with large Python files?
    │   ├── YES → Add filemap
    │   └── NO  → Skip filemap
    │
    ├── Want convenient search?
    │   ├── YES → Add search
    │   └── NO  → Use grep/find in bash
    │
    └── Want review before submit?
        ├── YES → Use review_on_submit_m
        └── NO  → Use submit
```

---

## Creating Custom Tools

See [`docs/usage/adding_custom_tools.md`](docs/usage/adding_custom_tools.md) for a full tutorial.

### Quick Example

1. **Create the bundle structure:**
```bash
mkdir -p tools/my_tool/bin
```

2. **Write the executable script** (`tools/my_tool/bin/my_command`):
```bash
#!/bin/bash
echo "Hello from my tool! Argument: $1"
```

3. **Create config.yaml** (`tools/my_tool/config.yaml`):
```yaml
tools:
  my_command:
    signature: "my_command <name>"
    docstring: "Says hello with the provided name"
    arguments:
      - name: name
        type: string
        description: "Name to greet"
        required: true
```

4. **Add to your config:**
```yaml
tools:
  bundles:
    - path: tools/my_tool
```

---

## Summary

- **Tools** are executable commands bundled with configuration
- **Bundles** are self-contained directories with scripts, config, and optional setup
- **`registry`** is essential for state management
- **`edit_anthropic`** provides the most important functionality (file editing)
- Other tools add convenience but can be replaced with- bash commands
- Tools are **configurable** - use only what you need for your workflow
