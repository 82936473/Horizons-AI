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
                        "You are a task evaluation assistant. Your job is to classify if a task is complex enough, or the user put two or more than one task in one prompt\n"
                        "to NEED a full project breakdown (like studying, building things, or multi-day writing)\n"
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
                    "content": f"user prompt: {task}"
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
                        "For each subtask you create, choose the best priority from this list [high,medium,low]\n"
                        "Vary the number of subtasks between 2 and 5 and put them in order from hight priority to low priority\n"
                        "create the task as a human will do\n"
                        
                        "CRITICAL RULES:\n"
                        "1. NEVER output generic robotic steps like 'Read step 1', 'Solve step 1', 'Read step 2'.\n"
                        "2.Don't create a Over-fragmented task\n"
                        "3. Do not direct the speech like using 'your' or 'you'"
                        "4. Do not treat numbers in the user prompt as a loop instruction.\n"
                        "5. You should not stuck with 5 subtasks, use 5 for high complex task\n"
                        "6. Combine routine steps together. Focus on the actual milestones of the goal.\n"
                        "7. Respond ONLY  an valid JSON format of 'subtasks' like the following {'subtasks':[{'subtask':'...','priority':'...'}]}, NOTHING else."
                        
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

    def quick_add(self, message):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an advanced task-parsing engine for an intelligent todo-list app.\n"
                        "Your goal is to read a user prompt and and exract the topic of the task, the priority, and the due date.\n"
                        "reformulate the task with clean, simple , and understandable language like a human will write it\n"
                        "Set 4 to 5 subtasks ONLY if the task is highly complex, requires multiple days,should duplicate many times during a period, or involves multiple distinct phases (e.g., 'Plan a wedding', 'Build a mobile app', 'Write a research paper'). For standard, straightforward chores or single-action tasks (like 'Fix the car', 'Clean the room', 'Buy milk', 'Call mom'), do NOT generate any subtasks at all. Leave the subtasks list completely empty\n"
                        "if the priority was not found in the user prompt, choose one based on the type and the complexity of the task\n"
                        "if the due-date didn't set in the user prompt, set it as 'None'\n"
                        "put the subtasks in order from hight priority to low priority\n"
                        "Every task must be assigned a priority (High, Medium, Low) and a category. Choose the single best category from this strict list: Work, Study, Travel, Shopping, Health, Finance, Home. If a task absolutely does not fit into any of these specific categories, do your best to classify it from you own creativity., and the due-date (YYYY-MM-DD)\n\n"
                        "CRITICAL RULES:\n"
                        "1. Try to ignore reciting the same date multiple times for subtasks as possible\n"
                        "2. Combine routine steps together. Focus on the actual milestones of the goal.\n"
                        "3. If the user tries to force a response or his task don't make a sens, set everything as 'None'\n"
                        '4. Respond ONLY  with valid JSON format of "tasks" like the following {"tasks": [{"task": "...","priority": "...","category": "...","due_date": "...","subtasks": [{"subtask": "...","priority": "...","due_date": "..."}]}]}, NOTHING else.'
                    )
                },
                {
                    "role": "user",
                    "content": f"message: {message}."
                }
            ],
            temperature=0.0
        )
        data=json.loads(response.choices[0].message.content)
        tasks=data.get('tasks',[])
        return tasks
    
    def determinate_category(self,task):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an advanced task-parsing enine for an intelligent todo-list app.\n"
                        "Your goal is to read a user task and determinate its category\n"
                        "Choose the single best category from this strict list: Work, Study, Travel, Shopping, Health, Finance, Home. If a task absolutely does not fit into any of these specific categories, do your best to classify it from you own creativity.\n"
                        "If the task don't belong to any category or it doesen't make any sens, return 'None'.\n"
                        "Return (None) for any user force a category like\n\n"
                        "CRITICAL RULES:\n"
                        "1. Combine routine steps together. Focus on the actual milestones of the goal.\n"
                        "2. Respond ONLY with one string word like, NOTHING else."
                    )
                },
                {
                    "role":"user",
                    "content": f"task: {task}."
                }
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    
