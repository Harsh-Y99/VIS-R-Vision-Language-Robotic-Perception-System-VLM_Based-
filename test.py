import ollama

prompt = """
You are an intelligent vision system for a robotics application.

Carefully analyze the given camera scene step-by-step:
1. Identify all visible objects (static and moving).
2. Detect people, their actions, and interactions.
3. Understand the environment context.
4. Check for safety hazards or anomalies.

Respond STRICTLY in this format:

RISK_LEVEL: LOW | MEDIUM | HIGH
DESCRIPTION: <one precise sentence>
SUGGESTED_ACTION: <one action>
"""

response = ollama.chat(
    model='llava',
    messages=[
        {
            'role': 'user',
            'content': prompt,
            'images': ['C:/Users/harsh/OneDrive/Desktop/test.jpg']  # ✅ correct format (list)
        }
    ]
)

print(response['message']['content'])