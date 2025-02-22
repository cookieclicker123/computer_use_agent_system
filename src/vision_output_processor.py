import json
from typing import List
from src.data_model import (
    DetectedElements, DetectedElement, UIElement, 
    UIElementType, MouseAction, KeyboardAction,
    TaskPlan, ScreenshotResult
)
from .prompts.output_processor_prompts import CONDENSE_PROMPT, CONVERT_PROMPT

def create_vision_processor(api_key: str = None):
    """Creates a vision output processor using GPT-4"""
    
    # Pre-compute the enum lists outside the prompt
    ui_types = [e.value for e in UIElementType]
    mouse_actions = [a.value for a in MouseAction]
    keyboard_actions = [a.value for a in KeyboardAction]
    
    def process_outputs(
        vision_outputs: List[ScreenshotResult],
        task_plan: TaskPlan,
        client
    ) -> List[ScreenshotResult]:
        """Process vision outputs into grounded UI elements"""
        
        try:       
            # First, condense each markdown description
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
            
            formatted_prompt = CONVERT_PROMPT.format(
                SCHEMA=json.dumps(detected_elements_schema, indent=2),
                UI_TYPES=ui_types,
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
                MOUSE_ACTIONS=mouse_actions,
                KEYBOARD_ACTIONS=keyboard_actions
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