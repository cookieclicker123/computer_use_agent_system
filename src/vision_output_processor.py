from typing import List, Dict
from src.data_model import (
    DetectedElements, DetectedElement, UIElement, 
    UIElementType, MouseAction, KeyboardAction,
    TaskPlan, ScreenshotResult
)
import json
import logging

logger = logging.getLogger(__name__)

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
        
        # Setup file logging
        file_handler = logging.FileHandler('debug_vision_processor.log', mode='w')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        try:
            # Debug what we're starting with
            logger.debug("=== Starting Vision Processing ===")
            logger.debug(f"Number of vision outputs: {len(vision_outputs)}")
            
            # First, condense each markdown description
            CONDENSE_PROMPT = """Extract and list the key UI elements from this description. For each element include:
1. What type of element it is
2. A brief description of its location/purpose
3. What actions can be taken with it

Format as a simple list:
- Element: [type] - [description] - Actions: [possible actions]"""

            condensed_elements = []
            for idx, result in enumerate(vision_outputs):
                logger.debug(f"\n=== Processing Screenshot {idx + 1}: {result.metadata.path} ===")
                logger.debug(f"Raw output length: {len(result.detected.raw_output) if result.detected.raw_output else 0}")
                logger.debug(f"Raw output preview: {result.detected.raw_output[:200]}..." if result.detected.raw_output else "No raw output")
                
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
                    logger.debug(f"\nCondensed elements for screenshot {idx + 1}:")
                    logger.debug(condensed)
                    condensed_elements.append(condensed)

            # Debug what we're sending to conversion
            logger.debug("\n=== Preparing Conversion ===")
            logger.debug("Combined condensed elements:")
            for idx, elements in enumerate(condensed_elements):
                logger.debug(f"\nScreenshot {idx + 1} elements:")
                logger.debug(elements)
            
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
            
            logger.debug("\nFinal Conversion Prompt:")
            logger.debug(formatted_prompt)
            
            # Process each screenshot
            for idx, result in enumerate(vision_outputs):
                if result.detected.raw_output:
                    logger.debug(f"\n=== Converting Screenshot {idx + 1}: {result.metadata.path} ===")
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": formatted_prompt},
                            {"role": "user", "content": result.detected.raw_output}
                        ],
                        temperature=0.1
                    )
                    
                    logger.debug(f"\nGPT Response for Screenshot {idx + 1}:")
                    logger.debug(response.choices[0].message.content)
                    
                    try:
                        # Strip markdown code block markers if present
                        json_content = response.choices[0].message.content
                        if json_content.startswith('```'):
                            # Find the first and last ``` and extract content between them
                            start = json_content.find('\n') + 1
                            end = json_content.rfind('```')
                            json_content = json_content[start:end].strip()
                        
                        elements_dict = json.loads(json_content)
                        logger.debug(f"\nParsed elements dict for Screenshot {idx + 1}:")
                        logger.debug(json.dumps(elements_dict, indent=2))
                        
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
                            
                            # Debug the assignment
                            logger.debug(f"\n=== Element Assignment for {result.metadata.path} ===")
                            logger.debug(f"Number of elements to assign: {len(detected_elements)}")
                            logger.debug("Elements being assigned:")
                            for elem in detected_elements:
                                logger.debug(f"  - Type: {elem.element.element_type}")
                                logger.debug(f"    Description: {elem.element.description}")
                            
                            # Assign elements
                            result.detected.elements = detected_elements
                            
                            # Verify assignment
                            logger.debug("\nVerifying assignment:")
                            logger.debug(f"Elements in result: {len(result.detected.elements)}")
                            logger.debug(f"Total count set to: {result.detected.total_count}")
                            
                            result.detected.total_count = len(detected_elements)
                            result.detected.highest_confidence = max(e.confidence for e in detected_elements)
                            
                            logger.debug(f"\nUpdated Screenshot {idx + 1} with:")
                            logger.debug(f"- Total elements: {result.detected.total_count}")
                            logger.debug("- Elements:")
                            for elem in detected_elements:
                                logger.debug(f"  * Type: {elem.element.element_type}")
                                logger.debug(f"    Description: {elem.element.description[:50]}...")
                                logger.debug(f"    Confidence: {elem.confidence}")
                                logger.debug(f"    Actions: {elem.possible_actions}")
                        
                    except Exception as e:
                        logger.error(f"Failed to parse response for Screenshot {idx + 1}: {str(e)}")
                        logger.error(f"Response was: {response.choices[0].message.content}")

            # Final validation of results
            logger.debug("\n=== Final Results Summary ===")
            for idx, result in enumerate(vision_outputs):
                logger.debug(f"\nScreenshot {idx + 1}: {result.metadata.path}")
                logger.debug(f"Total elements: {result.detected.total_count}")
                logger.debug(f"Has elements attribute: {hasattr(result.detected, 'elements')}")
                if hasattr(result.detected, 'elements'):
                    logger.debug(f"Elements list length: {len(result.detected.elements)}")
                    logger.debug("Element types:")
                    for elem in result.detected.elements:
                        logger.debug(f"- {elem.element.element_type}")
            
            return vision_outputs
            
        except Exception as e:
            logger.error(f"Error in process_outputs: {str(e)}")
            return vision_outputs
        
        finally:
            logger.removeHandler(file_handler)
    
    return process_outputs 