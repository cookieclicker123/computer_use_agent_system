import os
from datetime import datetime
from typing import Optional
import groq
from PIL import Image
import base64
from .data_model import (
    ScreenshotMetadata, ScreenshotResult, DetectedElements,
    UIElementType, MouseAction, KeyboardAction, ScreenshotFn
)
from .prompts.screenshot_agent_prompts import SCREENSHOT_VISION_PROMPT

def create_screenshot_agent(use_vision: bool = True, api_key: Optional[str] = None) -> ScreenshotFn:
    """Factory function that creates and returns a screenshot function"""
    
    
    # Initialize vision model client
    if use_vision:
        client = groq.Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
    
    def get_system_prompt() -> str:
        """Create system prompt with data model context"""
        return f"""You are a UI element detector. Analyze screenshots and return detected elements in this JSON format:
{{"elements": [
    {{
        "element_type": "<UIElementType enum: {[e.name for e in UIElementType]}>,
        "description": "location-based description",
        "confidence": float between 0-1,
        "actions": [<ActionType enums: {[a.name for a in MouseAction] + [a.name for a in KeyboardAction]}>],
        "bounds": [x, y, width, height] or null
    }}
]}}"""

    def extract_json_from_response(content: str) -> str:
        """Extract valid JSON from model response"""
        # Strip markdown code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        
        # Find complete JSON object
        start = content.find("{")
        if start == -1:
            raise ValueError("No JSON object found")
        
        # Track brackets to find matching end
        bracket_count = 0
        for i, char in enumerate(content[start:], start):
            if char == "{":
                bracket_count += 1
            elif char == "}":
                bracket_count -= 1
                if bracket_count == 0:
                    return content[start:i+1]
        
        raise ValueError("Incomplete JSON object")

    def get_detected_elements(image_path: str, client) -> DetectedElements:
        """Get detected elements from vision model analysis"""        
        try:
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            try:
                response = client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": SCREENSHOT_VISION_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ]
                )

            except Exception as api_error:
                print(f"API call failed: {str(api_error)}")
                print(f"Error type: {type(api_error)}")
                raise

            try:
                # Store raw output for later processing
                raw_output = response.choices[0].message.content
                # Return minimal DetectedElements to satisfy interface
                # Real processing happens in vision_output_processor
                result = DetectedElements(
                    elements=[],
                    total_count=0,
                    highest_confidence=0.0,
                    raw_output=raw_output
                )
                return result
                
            except Exception as parse_error:
                print(f"Failed to process vision model response: {str(parse_error)}")
                print(f"Error type: {type(parse_error)}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                raise
                
        except Exception as e:
            print(f"Error in get_detected_elements: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return DetectedElements()
    
    def screenshot_fn(image_path: str) -> ScreenshotResult:
        """Process a screenshot and return results"""        
        try:
            # Get image metadata
            image = Image.open(image_path)
            width, height = image.size
            metadata = ScreenshotMetadata(
                timestamp=datetime.now(),
                dimensions=(width, height),
                format='PNG',
                path=str(image_path),
                resolution=(width, height)
            )
            
            # Get detected elements
            if use_vision:
                detected = get_detected_elements(image_path, client)
            else:
                detected = DetectedElements()
            
            result = ScreenshotResult(
                metadata=metadata,
                detected=detected
            )
            return result
            
        except Exception as e:
            print(f"Error in screenshot_fn: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            raise
    
    return screenshot_fn