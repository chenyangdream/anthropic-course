from typing import final
from anthropic.resources import messages
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-6"
messages = []

temperature = 1.0
def chat(messages, temperature, system=None):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature
    }  
    if system:
        params["system"] = system
    message = client.messages.create(**params)
    return message.content[0].text

def add_user_message(messages, text):
    user_message = {"role": "user", "content": text}
    messages.append(user_message)

def add_assistant_message(messages, text):
    assistant_message = {"role": "assistant", "content": text}
    messages.append(assistant_message)

system = """
    你是一个电影编剧，写一个简单的剧本，200个字左右。
"""

messages = [
    {"role": "user", "content": f"[System Instructions]: {system} \n\n 写一个有趣的电影故事?"}
]

params = {
    "model": model,
    "max_tokens": 1000,
    "messages": messages,
    # "temperature": temperature,
    #"stream": True
}  

# with client.messages.stream(**params) as stream:

#     for text in stream.text_stream:
#         print(text, end="")

# final_message = stream.get_final_message()
# print(final_message.content[0].text)

add_user_message(messages, "Generate a very short event bridge rule as json")
add_assistant_message(messages, "```json")
answer = chat(messages, stop_sequences=["```"])
print(answer)
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
    