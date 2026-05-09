from typing import final
import json
from anthropic.resources import messages
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
#model = "claude-sonnet-4-6"
model = "claude-haiku-4-5"
messages = []

temperature = 1.0
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

params = {
    "model": model,
    "max_tokens": 1000,
    "messages": messages,
    "temperature": temperature,
    "stream": True
}

def generate_dataset():
    prompt ="""
Generate an evaluation dataset for a prompt evaluation. The dataset will be used to evaluate prompts
that generate Python, JSON, or Regex specifically for AWS-realted tasks. Generate an array of JSON object,
each respresenting task that require Python, JSON, or a Regex to complete.

Example output:
```json
[
    {
        "task": "Descripton of task",
    },
    ...additional
]
```
    * Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a regular experession.
    * Focus on tasks that do not requre writing much code.

    Please generate 3 objects.
"""

    messages = []

    add_user_message(messages, prompt)
    add_assistant_message(messages, "```json")
    text = chat(messages, stop_sequences=["```"])
    return json.loads(text)

dataset = generate_dataset()
print(dataset)

with open("dataset.json", "w") as f:
    json.dump(dataset, f, indent=2)

# with client.messages.stream(**params) as stream:

#     for text in stream.text_stream:
#         print(text, end="")

# final_message = stream.get_final_message()
# print(final_message.content[0].text)


# while True:
#     user_message = input("User:")
#     add_user_message(messages, user_message)
#     answer= chat(messages)
#     print("-----")
#     print(messages)
#     print("-----")
#     print("----")
#     print(answer)
#     print("----")
   
#     add_assistant_message(messages, answer)
    