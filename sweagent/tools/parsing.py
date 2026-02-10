"""Our parsers parse output from the LM into thoughts and actions.

For example, our most basic parser is the `ThoughtActionParser`.
It expects the model response to be a discussion followed by a command wrapped in backticks like so:

```
Let's look at the files in the current directory.

Action:
 ```
ls -l
 ```
```

For models that support function calling, we instead recommend using the `FunctionCallingParser`.

To use a specific parser, set the `parse_function` key in your tool config to the `type` field of the parser.

```yaml
agent:
    tools:
        ...
        parse_function:
            type: "thought_action"
```

Or from the command line: `--agent.tools.parse_function.type=thought_action`.

!!! note "Describing available tools"
    If you do not use the `FunctionCallingParser`, you need to include documentation about the available tools
    in your system prompt. You can use the `{{command_docs}}` variable to include the automatically generated
    documentation or explicitly describe the available tools.
    Also see [#1130](https://github.com/SWE-agent/SWE-agent/issues/1130).
"""

import json
import re
import textwrap
from abc import ABC, abstractmethod
from shlex import quote
from textwrap import dedent
from typing import Any, Literal

from jinja2 import Template
from pydantic import BaseModel

from sweagent.exceptions import FormatError, FunctionCallingFormatError
from sweagent.tools.commands import Command
from sweagent.tools.utils import _should_quote


class AbstractParseFunction(ABC):
    """
    Abstract class for parsing functions.
    We use get to generate the right parser based on the name of the parser.
    """

    error_message: str

    @abstractmethod
    def __call__(self, model_response, commands: list[Command], strict=False) -> tuple[str, str]:
        raise NotImplementedError

    @property
    def format_error_template(self):
        return textwrap.dedent(self.error_message)


# DEFINE NEW PARSING FUNCTIONS BELOW THIS LINE


class ThoughtActionParser(AbstractParseFunction, BaseModel):
    """
    Expects the model response to be a discussion followed by a command wrapped in backticks.
    Example:
    Let's look at the files in the current directory.
    ```
    ls -l
    ```
    """

    error_message: str = dedent("""\
    Your output was not formatted correctly. You must always include one discussion and one command as part of your response. Make sure you do not have multiple discussion/command tags.
    Please make sure your output precisely matches the following format:
    DISCUSSION
    Discuss here with yourself about what your planning and what you're going to do in this step.

    ```
    command(s) that you're going to run
    ```
    """)

    type: Literal["thought_action"] = "thought_action"
    """Type for (de)serialization. Do not change."""

    def __call__(self, model_response: dict, commands: list[Command], strict=False):
        """
        Parses the action from the output of the API call.
        We assume that the action is the last code block in the model_response.
        We also assume that the action is not nested within another code block.
        This is problematic if the model_response includes many unnamed ``` blocks.
        For instance:
        ```
        This is a code block.
        ```
        ```
        This is another code block.
        ```

        In this case, only the second code block will be parsed as the action.
        """
        code_block_pat = re.compile(r"^```(\S*)\s*\n|^```\s*$", re.MULTILINE)
        stack = []
        last_valid_block = None
        for match in code_block_pat.finditer(model_response["message"]):
            if stack and not match.group(1):  # Closing of a code block
                start = stack.pop()
                # Check if it's not nested within another block
                if not stack:
                    last_valid_block = (start, match)
            elif match.group(1) is not None:  # Opening of a code block
                stack.append(match)
        if last_valid_block:
            start, end = last_valid_block
            thought = model_response["message"][: start.start()] + model_response["message"][end.end() :]
            return thought, model_response["message"][start.end() : end.start()]
        msg = "No action found in model response."
        raise FormatError(msg)


class FunctionCallingParser(AbstractParseFunction, BaseModel):
    """Expects the model response to be a LiteLLM tool call."""

    error_message: str = dedent("""\
    {%- if error_code == "missing" -%}
    Your last output did not use any tool calls!
    Please make sure your output includes exactly _ONE_ function call!
    You must invoke the function directly using the function call format.
    You cannot invoke commands with ```, you have to use the function call format.
    If you think you have already resolved the issue, please submit your changes by running the `submit` command.
    If you think you cannot solve the problem, please run `exit_forfeit` (if available) or `submit`.
    Else, please continue with a new tool call!
    {%- elif error_code == "multiple" -%}
    Your last output included multiple tool calls!
    Please make sure your output includes a thought and exactly _ONE_ function call.
    {%- elif error_code == "unexpected_arg" -%}
    Your action could not be parsed properly: {{exception_message}}.
    Make sure your function call doesn't include any extra arguments that are not in the allowed arguments, and only use the allowed commands.
    {%- else -%}
    Your action could not be parsed properly: {{exception_message}}.
    {% endif %}
    """)

    type: Literal["function_calling"] = "function_calling"
    """Type for (de)serialization. Do not change."""

    def _parse_tool_call(self, tool_call: dict, commands: list[Command]):
        name = tool_call["function"]["name"]
        command = {c.name: c for c in commands}.get(name)
        if not command:
            msg = f"Command '{name}' not found in list of available commands."
            raise FunctionCallingFormatError(msg, "invalid_command")
        if not isinstance(tool_call["function"]["arguments"], dict):
            try:
                values = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError:
                msg = "Tool call arguments are not valid JSON."
                raise FunctionCallingFormatError(msg, "invalid_json")
        required_args = {arg.name for arg in command.arguments if arg.required}
        missing_args = required_args - values.keys()
        if missing_args:
            msg = f"Required argument(s) missing: {', '.join(missing_args)}"
            raise FunctionCallingFormatError(msg, "missing_arg")
        valid_args = {arg.name for arg in command.arguments}
        extra_args = set(values.keys()) - valid_args
        if command.end_name:
            # sometimes the model will include the end_name in the arguments - just ignore it
            extra_args.discard(command.end_name)
        if extra_args:
            msg = f"Unexpected argument(s): {', '.join(extra_args)}"
            raise FunctionCallingFormatError(msg, "unexpected_arg")

        def get_quoted_arg(value: Any) -> str:
            if isinstance(value, str):
                return quote(value) if _should_quote(value, command) else value
            # See https://github.com/SWE-agent/SWE-agent/issues/1159
            if value is None:
                return ""
            return value

        formatted_args = {
            arg.name: Template(arg.argument_format).render(value=get_quoted_arg(values[arg.name]))
            if arg.name in values
            else ""
            for arg in command.arguments
        }
        return command.invoke_format.format(**formatted_args).strip()

    def __call__(self, model_response: dict, commands: list[Command], strict=False):
        message = model_response["message"]
        tool_calls = model_response.get("tool_calls", None)
        if tool_calls is None or len(tool_calls) != 1:
            num_tools = len(tool_calls) if tool_calls else 0
            msg = (
                f"Expected exactly one tool call in model response - received {num_tools} "
                f"tool calls with message: {message}"
            )
            error_code = "missing" if num_tools == 0 else "multiple"
            raise FunctionCallingFormatError(msg, error_code, num_tools=num_tools)
        tool_call = tool_calls[0]
        action = self._parse_tool_call(tool_call, commands)
        return message, action


ParseFunction = ThoughtActionParser | FunctionCallingParser
