# Text Editor Tool example
# Converted from 005_text_editor_tool.ipynb with several bug fixes:
#   1. run_tool() now matches the correct tool name "str_replace_based_edit_tool"
#      (matches the schema declared in get_text_edit_schema()).
#   2. _validate_path() handles absolute paths sent by the model (e.g. "/main.py")
#      and uses os.path.commonpath() to prevent prefix-bypass.
#   3. tool_result content is no longer double-encoded by json.dumps when the
#      output is already a string.
#   4. Schema picker get_text_edit_schema() is now model-aware (3.5 / 3.7 / 4.x).

import json
import os
import shutil
from typing import List, Optional

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Client setup
# ---------------------------------------------------------------------------
load_dotenv()

client = Anthropic()
model = "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def add_user_message(messages, message):
    user_message = {
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(user_message)


def add_assistant_message(messages, message):
    assistant_message = {
        "role": "assistant",
        "content": message.content if isinstance(message, Message) else message,
    }
    messages.append(assistant_message)


def chat(messages, system=None, temperature=1.0, stop_sequences=None, tools=None):
    if stop_sequences is None:
        stop_sequences = []

    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }

    if tools:
        params["tools"] = tools

    if system:
        params["system"] = system

    return client.messages.create(**params)


def text_from_message(message):
    return "\n".join(
        [block.text for block in message.content if block.type == "text"]
    )


# ---------------------------------------------------------------------------
# Implementation of the TextEditorTool
# ---------------------------------------------------------------------------
class TextEditorTool:
    def __init__(self, base_dir: str = "", backup_dir: str = ""):
        self.base_dir = os.path.realpath(base_dir or os.getcwd())
        self.backup_dir = backup_dir or os.path.join(self.base_dir, ".backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def _validate_path(self, file_path: str) -> str:
        # The model often sends absolute paths like "/main.py". Treat them as
        # relative to base_dir so they don't escape the sandbox.
        if os.path.isabs(file_path):
            file_path = file_path.lstrip(os.sep)

        abs_path = os.path.realpath(os.path.join(self.base_dir, file_path))
        base_real = os.path.realpath(self.base_dir)

        try:
            common = os.path.commonpath([abs_path, base_real])
        except ValueError:
            common = ""

        if common != base_real:
            raise ValueError(
                f"Access denied: Path '{file_path}' is outside the allowed directory"
            )
        return abs_path

    def _backup_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return ""
        file_name = os.path.basename(file_path)
        backup_path = os.path.join(
            self.backup_dir, f"{file_name}.{os.path.getmtime(file_path):.0f}"
        )
        shutil.copy2(file_path, backup_path)
        return backup_path

    def _restore_backup(self, file_path: str) -> str:
        file_name = os.path.basename(file_path)
        backups = [
            f for f in os.listdir(self.backup_dir) if f.startswith(file_name + ".")
        ]
        if not backups:
            raise FileNotFoundError(f"No backups found for {file_path}")

        latest_backup = sorted(backups, reverse=True)[0]
        backup_path = os.path.join(self.backup_dir, latest_backup)

        shutil.copy2(backup_path, file_path)
        return f"Successfully restored {file_path} from backup"

    @staticmethod
    def _count_matches(content: str, old_str: str) -> int:
        return content.count(old_str)

    # ----- commands ---------------------------------------------------------
    def view(self, file_path: str, view_range: Optional[List[int]] = None) -> str:
        abs_path = self._validate_path(file_path)

        if os.path.isdir(abs_path):
            try:
                return "\n".join(os.listdir(abs_path))
            except PermissionError:
                raise PermissionError(
                    "Permission denied. Cannot list directory contents."
                )

        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")

        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")

        if view_range:
            start, end = view_range
            if end == -1:
                end = len(lines)
            selected_lines = lines[start - 1 : end]
            return "\n".join(
                f"{i}: {line}" for i, line in enumerate(selected_lines, start)
            )

        return "\n".join(f"{i}: {line}" for i, line in enumerate(lines, 1))

    def str_replace(self, file_path: str, old_str: str, new_str: str) -> str:
        abs_path = self._validate_path(file_path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")

        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()

        match_count = self._count_matches(content, old_str)
        if match_count == 0:
            raise ValueError(
                "No match found for replacement. Please check your text and try again."
            )
        if match_count > 1:
            raise ValueError(
                f"Found {match_count} matches for replacement text. "
                "Please provide more context to make a unique match."
            )

        # Backup before modifying
        self._backup_file(abs_path)

        new_content = content.replace(old_str, new_str)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return "Successfully replaced text at exactly one location."

    def create(self, file_path: str, file_text: str) -> str:
        abs_path = self._validate_path(file_path)

        if os.path.exists(abs_path):
            raise FileExistsError(
                "File already exists. Use str_replace to modify it."
            )

        parent = os.path.dirname(abs_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(file_text)

        return f"Successfully created {file_path}"

    def insert(self, file_path: str, insert_line: int, new_str: str) -> str:
        abs_path = self._validate_path(file_path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")

        # Backup before modifying
        self._backup_file(abs_path)

        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Make sure the previous last line ends with a newline before appending
        if lines and not lines[-1].endswith("\n"):
            lines[-1] = lines[-1] + "\n"

        if insert_line == 0:
            lines.insert(0, new_str + "\n")
        elif 0 < insert_line <= len(lines):
            lines.insert(insert_line, new_str + "\n")
        else:
            raise IndexError(
                f"Line number {insert_line} is out of range. "
                f"File has {len(lines)} lines."
            )

        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        return f"Successfully inserted text after line {insert_line}"

    def undo_edit(self, file_path: str) -> str:
        # Note: Claude 4.x text_editor tool no longer issues "undo_edit",
        # but we keep the implementation for older models (3.5 / 3.7).
        abs_path = self._validate_path(file_path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")

        return self._restore_backup(abs_path)


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------
text_editor_tool = TextEditorTool()


def run_tool(tool_name, tool_input):
    # Accept both the new (4.x) and legacy (3.5/3.7) names so we can switch
    # models without touching the dispatch logic.
    if tool_name in ("str_replace_based_edit_tool", "str_replace_editor"):
        command = tool_input["command"]
        if command == "view":
            return text_editor_tool.view(
                tool_input["path"], tool_input.get("view_range")
            )
        if command == "str_replace":
            return text_editor_tool.str_replace(
                tool_input["path"], tool_input["old_str"], tool_input["new_str"]
            )
        if command == "create":
            return text_editor_tool.create(
                tool_input["path"], tool_input["file_text"]
            )
        if command == "insert":
            return text_editor_tool.insert(
                tool_input["path"],
                tool_input["insert_line"],
                tool_input["new_str"],
            )
        if command == "undo_edit":
            return text_editor_tool.undo_edit(tool_input["path"])
        raise Exception(f"Unknown text editor command: {command}")

    raise Exception(f"Unknown tool name: {tool_name}")


def run_tools(message):
    tool_requests = [block for block in message.content if block.type == "tool_use"]
    tool_result_blocks = []

    for tool_request in tool_requests:
        try:
            tool_output = run_tool(tool_request.name, tool_request.input)
            content = (
                tool_output
                if isinstance(tool_output, str)
                else json.dumps(tool_output)
            )
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": content,
                "is_error": False,
            }
        except Exception as e:
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": f"Error: {e}",
                "is_error": True,
            }

        tool_result_blocks.append(tool_result_block)

    return tool_result_blocks


# ---------------------------------------------------------------------------
# Schema picker (per model version)
# ---------------------------------------------------------------------------
def get_text_edit_schema(model_name: str):
    # Claude 4.x family (Sonnet 4 / Opus 4 / Haiku 4 / 4.5 / 4.6 ...)
    if (
        model_name.startswith("claude-sonnet-4")
        or model_name.startswith("claude-opus-4")
        or model_name.startswith("claude-haiku-4")
        or model_name.startswith("claude-4")
    ):
        return {
            "type": "text_editor_20250728",
            "name": "str_replace_based_edit_tool",
        }

    # Claude 3.7
    if "3-7" in model_name or "3.7" in model_name:
        return {
            "type": "text_editor_20250124",
            "name": "str_replace_editor",
        }

    # Claude 3.5 (default fallback)
    return {
        "type": "text_editor_20241022",
        "name": "str_replace_editor",
    }


# ---------------------------------------------------------------------------
# Conversation loop
# ---------------------------------------------------------------------------
def run_conversation(messages):
    while True:
        response = chat(
            messages,
            tools=[get_text_edit_schema(model)],
        )

        add_assistant_message(messages, response)
        print(text_from_message(response))

        if response.stop_reason != "tool_use":
            break

        tool_results = run_tools(response)
        add_user_message(messages, tool_results)

    return messages


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    messages = []
    add_user_message(
        messages,
        """
        Open then main.py to calculate the pi to the 5th dight.
        The create a ./test.py file to test your implementation.
        """,
    )
    run_conversation(messages)
