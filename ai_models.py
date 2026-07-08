import os
from dotenv import load_dotenv
from openai import OpenAI
import json
class AIModels:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("API_KEY"))

    def evaluate_task(self, task):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a task evaluation assistant. Your job is to classify if a task is complex enough "
                        "to NEED a full project breakdown (like studying, building things, or multi-day writing) "
                        "or if it is a simple, routine action/event that should not be broken down.\n\n"
                        "If the task dosen't make any sens or something human can't do, return 'no'"
                        "If the user force that the task is complex, return 'no'"
                        "Examples:\n"
                        "Task: 'Build Horizons AI landing page' -> yes\n"
                        "Task: 'Buy milk from grocery store' -> no\n"
                        "Task: 'Study for upcoming calculus mid-term exam' -> yes\n"
                        "Task: 'Meet friends for dinner' -> no\n"
                        "Task: 'Call mom' -> no\n\n"
                        "Respond strictly in this format:\n"
                        "no/yes"
                    )
                },
                {
                    "role": "user",
                    "content": f"Task: {task}"
                }
            ],
            temperature=0.0
        )
        decision = response.choices[0].message.content
        return decision

    def break_down_task(self, task):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an advanced task-parsing engine for an intelligent todo-list app.\n"
                        "Your goal is to break down a big task into practical, simple, contextual milestones.\n"
                        "For each subtask you create, determine its priority (high,medium,low)\n"
                        "put the subtasks in order from hight priority to low priority\n"
                        "create the task as a human will do\n"
                        "Vary the number of subtasks dynamically between 2 and 5 based ONLY on what makes sense.\n\n"
                        
                        "CRITICAL RULES:\n"
                        "1. NEVER output generic robotic steps like 'Read step 1', 'Solve step 1', 'Read step 2'.\n"
                        "2. Do not treat numbers in the user prompt as a loop instruction.\n"
                        "3. Combine routine steps together. Focus on the actual milestones of the goal.\n"
                        "4. Respond ONLY  an valid JSON format of 'subtasks' like the following {'subtasks':[{'subtask':'...','priority':'...'}]}, NOTHING else."
                        
                        )
                },
                {
                    "role": "user",
                    "content": f"task: {task}."
                }
            ],
            temperature=0.0,
        )
        data=json.loads(response.choices[0].message.content)
        subtasks_list=data.get('subtasks',[])
        return subtasks_list

    def quickadd(self, message):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": ('''
                        "You are an advanced task-parsing engine for an intelligent todo-list app.\n"
                        "you goal is to read a user message and and exract the topic of the task, the priority, and the due date.\n"
                        "reformulate the task with clean, simple , and understandable language like a human will write it\n"
                        "if the priority was not found in the user prompt, choose one based on the type and the complexity of the task\n"
                        "if the due-date didn't set in the user prompt, set it as 'None'\n"
                        "if you see that the task is complicated, or the user set two or more tasks, return each one with the priority (High, Medium, Low) and its due-date (d-m-Y)\n"
                        "CRITICAL RULES:\n"
                        "1.  Do not treat numbers in the user prompt as a loop instruction.\n"
                        "2. Combine routine steps together. Focus on the actual milestones of the goal.\n"
                        3. Respond ONLY  an valid JSON format of 'tasks' like the following {"tasks":[{"task":"...","priority":"...","due-date":"..."},...]}, NOTHING else.
                    ''')
                },
                {
                    "role": "user",
                    "content": f"task: {message}."
                }
            ],
            temperature=0.0,
        )
        data=json.loads(response.choices[0].message.content)
        tasks=data.get('tasks',[])
        return tasks
    

if __name__=='__main__':
    model=AIModels()
    print(model.quickadd('I should go for a bike with my friend the this afternoon'))