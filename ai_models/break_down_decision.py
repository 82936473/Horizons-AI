import os
from dotenv import load_dotenv
from openai import OpenAI
import time as t
load_dotenv()
client = OpenAI(base_url="https://api.groq.com/openai/v1",api_key=os.environ.get("API_KEY"))
task="solve two questions of calculus"
s=t.time()
response = client.chat.completions.create(
    model="openai/gpt-oss-120b", 
    messages=[
        {"role": "system","content": (
                "You are a task evaluation assistant. Your job is to classify if a task is complex enough "
                "to NEED a full project breakdown (like studying, building things, or multi-day writing) "
                "or if it is a simple, routine action/event that should not be broken down.\n\n"
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
    temperature=0.0,
)
decision = response.choices[0].message.content
print(decision)
e = t.time()
print(f"Time taken: {e - s} seconds")