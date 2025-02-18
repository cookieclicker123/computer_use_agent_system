import logging
from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from src.data_model import (
    TaskPlan, Task, TaskAction, UIElement,
    MouseAction, KeyboardAction, SystemAction, 
    UIElementType, ValidationStatus, ValidationResult,
    taskPlannerFn
)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define enum mappings for system prompt
MOUSE_ACTIONS = {action: action.value for action in MouseAction}
KEYBOARD_ACTIONS = {action: action.value for action in KeyboardAction}
SYSTEM_ACTIONS = {action: action.value for action in SystemAction}
UI_ELEMENT_TYPES = {element: element.value for element in UIElementType}
VALIDATION_STATES = {status: status.value for status in ValidationStatus}

# Dynamic system prompt components
VALIDATION_SCHEMA = {
    "validation_result": {
        "status": "ValidationStatus enum (pending, success, failed, retry)",
        "message": "Optional explanation of validation result",
        "retry_count": "Number of retry attempts (default: 0)",
        "max_retries": "Maximum allowed retries (default: 3)"
    }
}

RETRY_SCHEMA = {
    "retry_strategy": {
        "max_attempts": "Maximum retry attempts (default: 3)",
        "delay_between_attempts": "Seconds to wait between retries (default: 1.0)",
        "fallback_action": "Optional alternative action if all retries fail"
    }
}

# Use our data models to define schemas
TASK_ACTION_SCHEMA = TaskAction.model_json_schema()
VALIDATION_RESULT_SCHEMA = ValidationResult.model_json_schema()
UI_ELEMENT_SCHEMA = UIElement.model_json_schema()
TASK_SCHEMA = Task.model_json_schema()

def create_task_planner(api_key: Optional[str] = None) -> taskPlannerFn:
    """Creates a task planner using GPT-4"""
    client = OpenAI(api_key=api_key)
    
    def planner(goal: str, context: Dict = None) -> TaskPlan:
        if not goal or goal.strip() == "":
            raise ValueError("Goal cannot be empty")
            
        USER_QUERY = goal.strip()
        logger.info(f"Planning tasks for goal: {USER_QUERY}")

        SYSTEM_PROMPT = f"""You are a computer automation task planner. Your role is to break down user goals into specific, actionable tasks.

User Query: '{USER_QUERY}'
High Level Goal: Search Google for '{USER_QUERY}' starting from VSCode terminal

IMPORTANT: Use these exact enum values:
Mouse Actions: {MOUSE_ACTIONS}
Keyboard Actions: {KEYBOARD_ACTIONS}
System Actions: {SYSTEM_ACTIONS}
UI Element Types: {UI_ELEMENT_TYPES}
Validation States: {VALIDATION_STATES}

Validation Schema: {VALIDATION_SCHEMA}
Retry Schema: {RETRY_SCHEMA}

Complete Example Task Plan:
{{
    "goal": "Search Google for 'neural networks' starting from VSCode terminal",
    "tasks": [
        {{
            "task_id": "navigate_to_desktop",
            "description": "Exit VSCode and return to desktop",
            "actions": [
                {{
                    "action_type": {KeyboardAction.CTRL_LEFT},
                    "target_element": {{
                        "element_type": {UIElementType.GENERIC},
                        "description": "VSCode window",
                        "confidence_required": 0.8
                    }},
                    "validation_result": {{
                        "status": {ValidationStatus.PENDING},
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
            "validation_status": {ValidationStatus.PENDING}
        }},
        {{
            "task_id": "launch_chrome",
            "description": "Open Google Chrome browser",
            "actions": [
                {{
                    "action_type": {MouseAction.DOUBLE_CLICK},
                    "target_element": {{
                        "element_type": {UIElementType.ICON},
                        "description": "Chrome browser icon",
                        "confidence_required": 0.9
                    }},
                    "validation_result": {{
                        "status": {ValidationStatus.PENDING},
                        "retry_count": 0,
                        "max_retries": 3
                    }},
                    "retry_strategy": {{
                        "max_attempts": 3,
                        "delay_between_attempts": 1.0
                    }}
                }}
            ],
            "dependencies": ["navigate_to_desktop"],
            "validation_status": {ValidationStatus.PENDING}
        }},
        {{
            "task_id": "perform_search",
            "description": "Enter search query",
            "actions": [
                {{
                    "action_type": {MouseAction.LEFT_CLICK},
                    "target_element": {{
                        "element_type": {UIElementType.SEARCH_BAR},
                        "description": "Google search bar",
                        "confidence_required": 0.8
                    }},
                    "validation_result": {{
                        "status": {ValidationStatus.PENDING},
                        "retry_count": 0,
                        "max_retries": 3
                    }},
                    "retry_strategy": {{
                        "max_attempts": 3,
                        "delay_between_attempts": 1.0
                    }}
                }},
                {{
                    "action_type": {KeyboardAction.TYPE},
                    "input_data": "{USER_QUERY}",
                    "target_element": {{
                        "element_type": {UIElementType.SEARCH_BAR},
                        "description": "Google search bar",
                        "confidence_required": 0.8
                    }},
                    "validation_result": {{
                        "status": {ValidationStatus.PENDING},
                        "retry_count": 0,
                        "max_retries": 2
                    }},
                    "retry_strategy": {{
                        "max_attempts": 2,
                        "delay_between_attempts": 1.0
                    }}
                }}
            ],
            "dependencies": ["launch_chrome"],
            "validation_status": {ValidationStatus.PENDING}
        }}
    ],
    "current_task_index": 0,
    "status": {ValidationStatus.PENDING}
}}

Always output valid JSON matching this exact structure and using the exact enum values shown above."""
            
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_QUERY}
                ],
                temperature=0.1,
                max_tokens=8192,
                response_format={ "type": "json_object" }
            )
            
            task_plan_dict = response.choices[0].message.content
            logger.debug(f"Raw GPT Response:\n{task_plan_dict}")
            
            try:
                return TaskPlan.model_validate_json(task_plan_dict)
            except Exception as e:
                logger.error(f"Validation Error Details:\n{str(e)}")
                raise ValueError(f"Failed to parse GPT response into TaskPlan: {e}")
                
        except Exception as e:
            logger.error(f"API Error: {str(e)}")
            raise RuntimeError(f"Failed to generate task plan: {e}")
    
    return planner 