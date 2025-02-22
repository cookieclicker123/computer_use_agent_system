import json
from typing import List
from src.data_model import (
    DetectedElements, DetectedElement, UIElement, 
    UIElementType, MouseAction, KeyboardAction,
    TaskPlan, ScreenshotResult
)

def create_vision_processor(api_key: str = None):
    """Creates a vision output processor using GPT-4"""
    
    # Pre-compute the enum lists outside the prompt
    ui_types = [e.value for e in UIElementType]
    mouse_actions = [a.value for a in MouseAction]
    keyboard_actions = [a.value for a in KeyboardAction]
    
    GROUNDING_PROMPT = """You are a UI element classifier. Your task is to convert natural language UI descriptions into structured elements matching our data model.

Available UI Element Types: {UI_TYPES}
Available Mouse Actions: {MOUSE_ACTIONS}
Available Keyboard Actions: {KEYBOARD_ACTIONS}

Given these vision model outputs and task plan, convert the descriptions into specific UI elements.
Each element must use exact types from the available options.

Vision Outputs:
{VISION_OUTPUTS}

Task Plan:
{TASK_PLAN}

Return valid JSON matching this EXACT structure:
{
    "elements": [
        {
            "element": {
                "element_type": "window",  # Must be one of: {UI_TYPES}
                "description": "original description"
            },
            "confidence": 0.9,  # float between 0-1
            "possible_actions": ["left_click"],  # Must be from: {MOUSE_ACTIONS} or {KEYBOARD_ACTIONS}
            "bounding_box": [x, y, width, height] or null
        }
    ]
}"""

    def process_outputs(
        vision_outputs: List[ScreenshotResult],
        task_plan: TaskPlan,
        client
    ) -> List[ScreenshotResult]:
        """Process vision outputs into grounded UI elements"""
        
        try:       
            # First, condense each markdown description
            CONDENSE_PROMPT = """Extract and list the key UI elements from this description. For each element include:
1. What type of element it is
2. A brief description of its location/purpose
3. What actions can be taken with it

Format as a simple list:
- Element: [type] - [description] - Actions: [possible actions]"""

            condensed_elements = []
            for idx, result in enumerate(vision_outputs):                
                if result.detected.raw_output:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": CONDENSE_PROMPT},
                            {"role": "user", "content": result.detected.raw_output}
                        ],
                        temperature=0.1
                    )
                    condensed = response.choices[0].message.content
                    condensed_elements.append(condensed)
            
            # Get the complete schema
            detected_elements_schema = DetectedElements.model_json_schema()
            
            CONVERT_PROMPT = """Convert these UI elements into our data model. You MUST map each element type and action to these exact values:

ELEMENT TYPE MAPPING RULES:
- Text input/field → "text_input"
- Menu/Navigation → "menu_bar"
- Image/Logo → "icon"
- Window/Panel → "window"
- Button/Control → "button"
- Search box → "search_bar"

No other element types are allowed. Map each element to its closest match from: {UI_TYPES}

ACTION MAPPING RULES:
Mouse Actions: {MOUSE_ACTIONS}
- Click/Select → "left_click"
- Right Click/Context → "right_click"
- Double Click/Open → "double_click"

Keyboard Actions: {KEYBOARD_ACTIONS}
- Type/Input → "type"
- Enter/Submit → "enter"
- Delete/Remove → "backspace"

DetectedElements Schema:
{SCHEMA}

Return JSON matching this EXACT DetectedElements example:
{EXAMPLE}"""

            formatted_prompt = CONVERT_PROMPT.format(
                SCHEMA=json.dumps(detected_elements_schema, indent=2),
                UI_TYPES=[e.value for e in UIElementType],
                EXAMPLE=DetectedElements(
                    elements=[
                        DetectedElement(
                            element=UIElement(
                                element_type=UIElementType.WINDOW,
                                description="Chrome browser window"
                            ),
                            confidence=0.9,
                            possible_actions=[MouseAction.LEFT_CLICK],
                            bounding_box=None
                        ),
                        DetectedElement(
                            element=UIElement(
                                element_type=UIElementType.SEARCH_BAR,
                                description="Google search input"
                            ),
                            confidence=0.95,
                            possible_actions=[MouseAction.LEFT_CLICK, KeyboardAction.TYPE],
                            bounding_box=None
                        )
                    ]
                ).model_dump_json(indent=2),
                MOUSE_ACTIONS=[a.value for a in MouseAction],
                KEYBOARD_ACTIONS=[a.value for a in KeyboardAction]
            )        
            
            # Process each screenshot
            for idx, result in enumerate(vision_outputs):
                if result.detected.raw_output:                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": formatted_prompt},
                            {"role": "user", "content": result.detected.raw_output}
                        ],
                        temperature=0.1
                    )
                    
                    try:
                        # Strip markdown code block markers if present
                        json_content = response.choices[0].message.content
                        if json_content.startswith('```'):
                            # Find the first and last ``` and extract content between them
                            start = json_content.find('\n') + 1
                            end = json_content.rfind('```')
                            json_content = json_content[start:end].strip()
                        
                        elements_dict = json.loads(json_content)

                        if isinstance(elements_dict, dict) and "elements" in elements_dict:
                            detected_elements = [
                                DetectedElement(
                                    element=UIElement(**e["element"]),
                                    confidence=e["confidence"],
                                    possible_actions=e["possible_actions"],
                                    bounding_box=e["bounding_box"]
                                )
                                for e in elements_dict["elements"]
                            ]                           
                            
                            # Assign elements
                            result.detected.elements = detected_elements
                            
                            result.detected.total_count = len(detected_elements)
                            result.detected.highest_confidence = max(e.confidence for e in detected_elements)
                        
                    except Exception as e:
                        print(f"Failed to parse response for Screenshot {idx + 1}: {str(e)}")
                        print(f"Response was: {response.choices[0].message.content}")

            
            return vision_outputs
            
        except Exception as e:
            print(f"Error in process_outputs: {str(e)}")
            return vision_outputs
        
        finally:
            print("Error in process_outputs: {str(e)}")
    
    return process_outputs 