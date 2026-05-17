# Imports
import json
import concurrent.futures
import re
from textwrap import dedent
from statistics import mean
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic()
#model = "claude-sonnet-4-6"
model = "claude-haiku-4-5"

def chat(messages, system=None, temperature=1.0, stop_sequences=[]):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature
    }

    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences

    message = client.messages.create(**params)
    return message.content[0].text

def add_user_message(messages, text):
    user_message = {"role": "user", "content": text}
    messages.append(user_message)

def add_assistant_message(messages, text):
    assistant_message = {"role": "assistant", "content": text}
    messages.append(assistant_message)


def generate_dataset():
    prompt ="""
Generate an evaluation dataset for a prompt evaluation. The dataset will be used to evaluate prompts
that generate Python, JSON, or Regex specifically for AWS-related tasks. Generate an array of JSON object,
each representing task that require Python, JSON, or a Regex to complete.

Example output:
```json
[
    {
        "task": "Descripton of task",
        "format": "json" or "python" or "regex",
        "solution_criteria": "Must include runtime, memory size, timeout and basic structure for AWS Lambda function"
    },
    ...additional
]
```
    * Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a regular expression.
    * Focus on tasks that do not require writing much code.

    Please generate 3 objects.
"""

    messages = []

    add_user_message(messages, prompt)
    add_assistant_message(messages, "```json")
    text = chat(messages, stop_sequences=["```"])
    return json.loads(text)


if __name__ == "__main__":
    dataset = generate_dataset()
    print(dataset)

    with open("dataset.json", "w") as f:
        json.dump(dataset, f, indent=2)
