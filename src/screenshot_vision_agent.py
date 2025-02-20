import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import groq
from PIL import Image
import base64
import json
import logging
from .data_model import (
    ScreenshotMetadata, ScreenshotResult, DetectedElement, DetectedElements,
    UIElement, UIElementType, ActionType, ValidationStatus,
    MouseAction, KeyboardAction, ScreenshotFn
)

logger = logging.getLogger(__name__)

def create_screenshot_agent(use_vision: bool = True, api_key: Optional[str] = None) -> ScreenshotFn:
    """Factory function that creates and returns a screenshot function"""
    
    logger.info("Creating screenshot agent with vision=%s", use_vision)
    
    # Initialize vision model client
    if use_vision:
        client = groq.Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        logger.info("Initialized Groq client")
    
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
        logger.info(f"Analyzing image: {image_path}")
        
        try:
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                logger.debug("Successfully encoded image to base64")
            
            user_prompt = """Analyze this screenshot and describe the UI elements you see.
For each element, describe:
1. What type of UI element it is
2. Its location and appearance
3. What actions a user could take with it
4. Any text or labels visible

Be specific and detailed but use natural language."""

            logger.info("Sending request to vision model")
            logger.debug(f"Using prompt: {user_prompt}")
            
            try:
                response = client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
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
                logger.info("Received response from vision model")
                logger.debug(f"Raw response: {response}")
                
            except Exception as api_error:
                logger.error(f"API call failed: {str(api_error)}")
                logger.error(f"Error type: {type(api_error)}")
                raise

            try:
                # Store raw output for later processing
                raw_output = response.choices[0].message.content
                logger.info("Successfully extracted raw output")
                logger.debug(f"Raw output content: {raw_output}")
                
                # Return minimal DetectedElements to satisfy interface
                # Real processing happens in vision_output_processor
                result = DetectedElements(
                    elements=[],
                    total_count=0,
                    highest_confidence=0.0,
                    raw_output=raw_output
                )
                logger.info("Created DetectedElements object")
                return result
                
            except Exception as parse_error:
                logger.error(f"Failed to process vision model response: {str(parse_error)}")
                logger.error(f"Error type: {type(parse_error)}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                raise
                
        except Exception as e:
            logger.error(f"Error in get_detected_elements: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return DetectedElements()
    
    def screenshot_fn(image_path: str) -> ScreenshotResult:
        """Process a screenshot and return results"""
        logger.info(f"Processing screenshot: {image_path}")
        
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
            logger.info(f"Got image metadata: {metadata}")
            
            # Get detected elements
            if use_vision:
                logger.info("Using vision model for element detection")
                detected = get_detected_elements(image_path, client)
            else:
                logger.info("Vision disabled, returning empty elements")
                detected = DetectedElements()
            
            result = ScreenshotResult(
                metadata=metadata,
                detected=detected
            )
            logger.info("Successfully created ScreenshotResult")
            return result
            
        except Exception as e:
            logger.error(f"Error in screenshot_fn: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    return screenshot_fn

# Example usage:
# screenshot_fn = create_screenshot_agent(use_vision=True, api_key="your-api-key")
# result = screenshot_fn("path/to/screenshot.png") 