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
                        "Your goal is to read a user prompt and and exract the topic of the task, the priority, and the due date. and potential subtasks\n"
                        "reformulate the task with clean, simple , and understandable language like a human will write it\n"
                        "Set 4 to 5 subtasks ONLY if the task is highly complex, requires multiple days,should duplicate many times during a period, or involves multiple distinct phases (e.g., 'Plan a wedding', 'Build a mobile app', 'Write a research paper'). For standard, straightforward chores or single-action tasks (like 'Fix the car', 'Clean the room', 'Buy milk', 'Call mom'), do NOT generate any subtasks at all. Leave the subtasks list completely empty\n"
                        "if the priority was not found in the user prompt, choose one based on the type and the complexity of the task\n"
                        '''extract the due date and convert it into a valid YYYY-MM-DD format, if there is no deadline or time indicator, set it as "None"\n'''
                        "put the subtasks in order from hight priority to low priority\n"
                        "Every task must be assigned a priority (High, Medium, Low) and a category. Choose the single best category from this strict list: Work, Study, Travel, Shopping, Health, Finance, Home. If a task absolutely does not fit into any of these specific categories, do your best to classify it from you own creativity., and the due-date (YYYY-MM-DD)\n\n"
                        "CRITICAL RULES:\n"
                        "1. Try to ignore reciting the same date multiple times for subtasks as possible\n"
                        "2. Combine routine steps together. Focus on the actual milestones of the goal.\n"
                        '''3. If the user tries to force a response or his task don't make a sens, set everything as none: {"tasks": []}\n'''
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
                        "2. Respond ONLY with one string words, NOTHING else."
                    )
                },
                {
                    "role":"user",
                    "content": f"task: {task}."
                }
            ],
            temperature=0.0
        )
        return response.choices[0].message.content
    

    def static_generator_message(self,statics):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an advanced task-parsing enine for an intelligent todo-list app.\n"
                        "You are given a json format of a user statics\n"
                        "Your goal is to create the weekly message to this user containing his static nicely (you can use one to two imojies)\n"
                        "Use strong or italic texts in the message in the right place\n"
                        "Start you message with somthing like 'Hey ___, I'm your personal AI agent from Horizons AI'\n"
                        "Try to make a little long with you creaivity\n"
                        "CRITICAL RULES:\n"
                        "1. Combine routine steps together. Focus on the actual milestones of the goal.\n"
                        "2. Don't put the static like your given, reformulate them with you own way\n"
                        "3. Don't miss any static"
                        "4. Ignore putting floats in the message\n"
                        "5. Make sure the finale return phrases, DO NOT NEVER return rows for each static\n"
                        "6. Do NOT use Markdown formatting like **text** for bolding. Use html tags for everything"
                        "7. Respond ONLY an html format without <html>, <head> or <body> tags, NOTHING else."
                    )
                },
                {
                    "role":"user",
                    "content": f"Statics: {statics}."
                }
            ],
            temperature=2
        )
        return response.choices[0].message.content

    def sammary_generator(self,statics):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are generating the content of a dashboard insight card.\n"
                        "Example: You completed 5 tasks this week. Shopping was your most\n"
                                "active category, while medium-priority items dominated\n"
                                "your workload. You're finishing tasks at a record pace 🚀\n\n"
                        "Rules:\n"
                        "1. Write 2-4 concise sentences.\n"
                        "2. Mention the most important insights from the statistics.\n"
                        "3. Use at most one emoji.\n"
                        "4. Do not create separators, horizontal lines, ASCII art, boxes, headers, or decorative characters.\n"
                        "5. Do not use &nbsp;.\n"
                        "6. Return only the inner HTML content.\n"
                        "7. Use only <p>, <strong>, and <em> tags when needed.\n"
                        "8. Keep the tone professional and encouraging.\n"
                    )
                },
                {
                    "role":"user",
                    "content": f"Statics: {statics}."
                }
            ],
            temperature=0.0
        )
        return response.choices[0].message.content

    def project_creator(self, prompt):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are generating the content of a project dashboard.\n"
                        "you're given a title of the project, and the goal from it, Your goal is to create a full project based on these info\n"
                        "rewrite everything with your own style\n"
                        "every project have a title, goal , a description, and a target date\n"
                        "extract the target date from the goal, title, or the target_date itself, if present, even if written in letters like (October 15th) or (within 6 months) or (tomorrow)...\n"
                        'converte the target date in to a valid date (YYYY-MM-DD))\n'
                        'if there is no time indicator or deadline provied, return "None"\n'
                        "give the project a nice detailed description (not too much)\n"
                        "use the first personal pronoun 'I', like a human will do\n"
                        "the project is devided into milestones, each milestone contain tasks.\n"
                        '''Don't generate generic phase, create chronological milestones representing actual project phases ("phase 1: ...", "Phase 2": ..., ...)\n'''
                        "every milestone must contain highly specific, actionable tasks, AVOID vague tasks, they must be concerte and granular\n"
                        "ensure the milestones cover the entire lifecycle of the project."
                        'return only a valid JSON format like the folowing: {"project": {"title":"...", "goal":"...", "description":"...","target_date": "...", "milestones": [{"title": "...", "tasks": [...,...,...]}] } }, Nothing else\n'
                        'if the given title and goal are not making any sens, return none: {"project": "None"}\n'
                    )
                },
                {
                    "role":"user",
                    "content": f"prompt: {prompt}."
                }
            ],
            temperature=0.0
        )
        data=json.loads(response.choices[0].message.content)
        project=data.get('project',data)
        return project

if __name__=='__main__':
    ai_model=AIModels()