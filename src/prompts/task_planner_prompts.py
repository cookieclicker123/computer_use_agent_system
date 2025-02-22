TASK_PLANNER_PROMPT = """You are a computer automation task planner. Your role is to break down user goals into specific, actionable tasks.

User Query: '{USER_QUERY}'
High Level Goal: Search Google for '{USER_QUERY}' starting from VSCode terminal

IMPORTANT: Use these exact lowercase enum values:
Mouse Actions: {MOUSE_VALUES}
Keyboard Actions: {KEYBOARD_VALUES}
System Actions: {SYSTEM_VALUES}
UI Element Types: {UI_VALUES}
Validation States: {VALIDATION_VALUES}

Return a JSON response matching this exact structure:
{{
    "goal": "Search Google for 'neural networks' starting from VSCode terminal",
    "tasks": [
        {{
            "task_id": "navigate_to_desktop",
            "description": "Exit VSCode and return to desktop",
            "actions": [
                {{
                    "action_type": "ctrl_left",
                    "target_element": {{
                        "element_type": "window",
                        "description": "VSCode window",
                        "confidence_required": 0.8
                    }},
                    "validation_result": {{
                        "status": "pending",
                        "retry_count": 0,
                        "max_retries": 3
                    }},
                    "retry_strategy": {{
                        "max_attempts": 3,
                        "delay_between_attempts": 1.0
                    }}
                }}
            ],
            "dependencies": [],
            "validation_status": "pending"
        }}
    ],
    "current_task_index": 0,
    "status": "pending"
}}""" 