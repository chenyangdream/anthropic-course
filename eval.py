import ast
import json
import re

from anthropic import Anthropic
from anthropic.resources import messages
from dotenv import load_dotenv
from statistics import mean
from typing import final

load_dotenv()

client = Anthropic()
#model = "claude-sonnet-4-6"
model = "claude-haiku-4-5"
messages = []

temperature = 1.0

def add_user_message(messages, text):
    user_message = {"role": "user", "content": text}
    messages.append(user_message)

def add_assistant_message(messages, text):
    assistant_message = {"role": "assistant", "content": text}
    messages.append(assistant_message)

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


def validate_json(text):
    try:
        json.loads(text.strip())
        return 10
    except json.JSONDecodeError:
        return 0

def validate_python(text):
    try:
        ast.parse(text.strip())
        return 10
    except SyntaxError:
        return 0

def validate_regex(text):
    try:
        re.compile(text.strip())
        return 10
    except re.error:
        return 0
    
def grade_by_code(response, test_case):
    if test_case["format"] == "json":
        return validate_json(response)
    elif test_case["format"] == "python":
        return validate_python(response)
    else:
        return validate_regex(response)

def run_prompt(test_case):
    prompt = f"""
Please solve the following task:

{test_case["task"]}

* Response only with Python, JOSN, or a plain Regex
* Do not add any comments or commentary or explanations
"""

    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```code")
    output = chat(messages, stop_sequences=["```"])
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

Criteria you should use the evaluate:
<criteria>
{test_case["solution_criteria"]}
</criteria>

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
    model_score = model_grade["score"]
    reasoning = model_grade["reasoning"]

    code_score = grade_by_code(output, test_case)
    score = (model_score + code_score) / 2.0

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
                "task": "task description",
                "format": "json",
                "solution_criteria": "Must include AWSTemplateFormatVersion, Resources section with AWS::S3::Bucket, VersioningConfiguration set to Enabled, and PublicAccessBlockConfiguration with all block settings set to true"
            },
            {
                "task": "task description",
                "format": "json",
                "solution_criteria": "Must include AWSTemplateFormatVersion, Resources section with AWS::S3::Bucket, VersioningConfiguration set to Enabled, and PublicAccessBlockConfiguration with all block settings set to true"
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

print(json.dumps(results, indent=2))
