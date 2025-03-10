from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from src.data_model import (
    TaskPlan, Task, TaskAction, UIElement,
    MouseAction, KeyboardAction, SystemAction, 
    UIElementType, ValidationStatus, ValidationResult,
    taskPlannerFn
)
from src.prompts.task_planner_prompts import TASK_PLANNER_PROMPT

load_dotenv()



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
        
        try:    
            # Pre-compute the lists
            mouse_action_values = [a.value for a in MouseAction]
            keyboard_action_values = [a.value for a in KeyboardAction]
            system_action_values = [a.value for a in SystemAction]
            ui_type_values = [e.value for e in UIElementType]
            validation_state_values = [s.value for s in ValidationStatus]

            try:
                formatted_prompt = TASK_PLANNER_PROMPT.format(
                    USER_QUERY=USER_QUERY,
                    MOUSE_VALUES=mouse_action_values,
                    KEYBOARD_VALUES=keyboard_action_values,
                    SYSTEM_VALUES=system_action_values,
                    UI_VALUES=ui_type_values,
                    VALIDATION_VALUES=validation_state_values
                )
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": formatted_prompt},
                        {"role": "user", "content": USER_QUERY}
                    ],
                    temperature=0.1,
                    max_tokens=8192,
                    response_format={ "type": "json_object" }
                )
                
                task_plan_dict = response.choices[0].message.content                
                try:
                    return TaskPlan.model_validate_json(task_plan_dict)
                except Exception as e:
                    print(f"Validation Error Details:\n{str(e)}")
                    raise ValueError(f"Failed to parse GPT response into TaskPlan: {e}")
                
            except Exception as e:
                print(f"API Error: {str(e)}")
                raise RuntimeError(f"Failed to generate task plan: {e}")
                
        except Exception as e:
            print(f"Error in enum processing: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            raise

    return planner 