from typing import final
import json
from anthropic.resources import messages
from dotenv import load_dotenv
from statistics import mean
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

def run_prompt(test_case):
    prompt = f"""
Please solve the following task:

{test_case["task"]}
"""

    messages = []
    add_user_message(messages, prompt)
    output = chat(messages)
    return output

def grade_by_model(test_case, output):
    # Create evaluation prompt
    eval_prompt = f"""
You are an expert AWS code reviewer. Your task is to evaluate the following AI-generated solution.

Original Task:
<task>
{test_case["task"]}
</task>

Solution to Evaluate:
<solution>
{output}
</solution>

Output Format
Provide your evaluation as a structured JSON object with the following fields, in this specific order:
- "strengths": An array of 1-3 key strengths
- "weaknesses": An array of 1-3 key areas for improvement
- "reasoning": A concise explanation of your overall assessment
- "score": A number between 1-10

Respond with JSON. Keep your response concise and direct.
Example response shape:
{{
    "strengths": string[],
    "weaknesses": string[],
    "reasoning": string,
    "score": number
}}
"""

    messages = []
    add_user_message(messages, eval_prompt)
    add_assistant_message(messages, "```json")
    eval_response = chat(messages, stop_sequences=["```"])
    print("eval_response", eval_response)
    return json.loads(eval_response)


def run_test_case(test_case):
    """Calls run_prompt, then grades the result"""
    output = run_prompt(test_case)

    model_grade = grade_by_model(test_case, output)
    score = model_grade["score"]
    reasoning = model_grade["reasoning"]

    return {
        "output": output,
        "test_case": test_case,
        "score": score,
        "reasoning": reasoning
    }

def run_eval(dataset):
    """
        dataset = [
            {
                "task": "task description"
            },
            {
                "task": "task description"
            }
        ]
        dataset is a list of testcases
        Loads the dataset and calls run_test_case with each case
    """
    results = []
    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)
    avarage_score = mean([result["score"] for result in results])
    print(avarage_score)

    return results

with open("dataset.json", "r") as f:
    dataset = json.load(f)

results = run_eval(dataset)
