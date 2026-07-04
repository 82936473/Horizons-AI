import os
from dotenv import load_dotenv
from openai import OpenAI
# import json
class TaskBreakdown:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.environ.get("API_KEY"))

    def break_down_task(self, task):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an advanced task-parsing engine for an intelligent todo-list app.\n"
                        "Your goal is to break down a big task into practical, contextual milestones.\n"
                        "For each subtask you create, determine its priority (high,medium,low)\n"
                        "create the task like a human will do\n"
                        "Vary the number of subtasks dynamically between 1 and 4 based ONLY on what makes sense.\n\n"
                        
                        "CRITICAL RULES:\n"
                        "1. NEVER output generic robotic steps like 'Read step 1', 'Solve step 1', 'Read step 2'.\n"
                        "2. Do not treat numbers in the user prompt as a loop instruction.\n"
                        "3. Combine routine steps together. Focus on the actual milestones of the goal.\n\n"
                        
                        "Respond ONLY  an array of 'subtasks' like the following [['subtask 1','high'],['subtask 2','medium'],['subtask 3','low']...], NOTHING else."
                    )
                },
                {
                    "role": "user",
                    "content": f"task: {task}."
                }
            ],
            temperature=0.0,
        )
        content = response.choices[0].message.content
        return content
class TaskDecision:
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