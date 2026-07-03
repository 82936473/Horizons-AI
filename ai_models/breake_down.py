import os
import json
from dotenv import load_dotenv
import time as t #!#!
from openai import OpenAI
load_dotenv()
client = OpenAI(base_url="https://api.groq.com/openai/v1",api_key=os.environ.get("API_KEY"))
# def break_down_task(task):
task="solve two questions of calculus"
s=t.time() #!#!
response = client.chat.completions.create(
    model="openai/gpt-oss-120b", 
    messages=[
        {
            "role": "system", 
            "content": (
                "You are an advanced task-parsing engine for an intelligent todo-list app.\n"
                "Your goal is to break down a big task into practical, contextual milestones. "
                "Vary the number of subtasks dynamically between 1 and 4 based ONLY on what makes sense.\n\n"
                
                "CRITICAL RULES:\n"
                "1. NEVER output generic robotic steps like 'Read step 1', 'Solve step 1', 'Read step 2'.\n"
                "2. Do not treat numbers in the user prompt as a loop instruction.\n"
                "3. Combine routine steps together. Focus on the actual milestones of the goal.\n\n"
                
                "Respond ONLY with a valid JSON object containing an array of 'subtasks' like the following {'subtasks':['subtask 1','subtask 2'...]}."
                )
        },
        {
            "role": "user", 
            "content": f"task: {task}."
        }
    ],
    response_format={"type": "json_object"},
    temperature=0.0,
    max_tokens=200
)
raw_content = response.choices[0].message.content
subtasks = json.loads(raw_content)['subtasks']
# return subtasks
for i in subtasks:
    print(i)
e=t.time() #!#!
print(f"Time taken: {e - s} seconds")
