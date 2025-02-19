from pathlib import Path
from datetime import datetime
from typing import Dict
from PIL import Image
from src.data_model import (
    ScreenshotMetadata, ScreenshotResult, DetectedElement, DetectedElements,
    UIElement, UIElementType, ValidationStatus,
    MouseAction, KeyboardAction, ScreenshotFn
)

def create_screenshot_agent(mock: bool = True) -> ScreenshotFn:
    """Factory function that creates and returns a screenshot function"""
    
    # Setup fixtures path and verify mock screenshots exist
    fixtures_path = Path(__file__).parent.parent / "fixtures" / "test_screenshots"
    mock_screenshots = {
        "vscode": fixtures_path / "vscode.png",
        "desktop": fixtures_path / "desktop.png",
        "chrome": fixtures_path / "google_chrome.png"
    }
    
    # Track current context for mock sequence
    current_context = {"index": 0}
    contexts = ["vscode", "desktop", "chrome"]
    
    # Debug path information
    print(f"Looking for screenshots in: {fixtures_path}")
    for name, path in mock_screenshots.items():
        print(f"Checking for {name} screenshot at: {path}")
        if not path.exists():
            raise FileNotFoundError(f"Mock screenshot not found: {path}")
    
    def get_mock_elements(context: str) -> DetectedElements:
        """Return mock detected elements based on context"""
        elements_data = {
            "vscode": [
                DetectedElement(
                    element=UIElement(
                        element_type=UIElementType.WINDOW,
                        description="VSCode Window"
                    ),
                    confidence=0.95,
                    possible_actions=[KeyboardAction.CTRL_LEFT],
                    bounding_box=(0, 0, 1920, 1080)
                ),
                DetectedElement(
                    element=UIElement(
                        element_type=UIElementType.TERMINAL,
                        description="Integrated Terminal"
                    ),
                    confidence=0.92,
                    possible_actions=[KeyboardAction.TYPE, MouseAction.LEFT_CLICK],
                    bounding_box=(0, 800, 1920, 280)
                )
            ],
            "desktop": [
                DetectedElement(
                    element=UIElement(
                        element_type=UIElementType.ICON,
                        description="Chrome Browser Icon"
                    ),
                    confidence=0.98,
                    possible_actions=[MouseAction.DOUBLE_CLICK, MouseAction.RIGHT_CLICK],
                    bounding_box=(100, 100, 64, 64)
                ),
                DetectedElement(
                    element=UIElement(
                        element_type=UIElementType.TASKBAR,
                        description="macOS Dock"
                    ),
                    confidence=0.96,
                    possible_actions=[MouseAction.LEFT_CLICK],
                    bounding_box=(0, 1000, 1920, 80)
                )
            ],
            "chrome": [
                DetectedElement(
                    element=UIElement(
                        element_type=UIElementType.SEARCH_BAR,
                        description="Google Search Bar"
                    ),
                    confidence=0.99,
                    possible_actions=[MouseAction.LEFT_CLICK, KeyboardAction.TYPE],
                    bounding_box=(400, 300, 600, 40)
                ),
                DetectedElement(
                    element=UIElement(
                        element_type=UIElementType.BUTTON,
                        description="Search Button"
                    ),
                    confidence=0.97,
                    possible_actions=[MouseAction.LEFT_CLICK],
                    bounding_box=(1000, 300, 100, 40)
                )
            ]
        }
        
        elements = elements_data.get(context, [])
        highest_confidence = max((e.confidence for e in elements), default=0.0)
        
        return DetectedElements(
            elements=elements,
            total_count=len(elements),
            highest_confidence=highest_confidence
        )
    
    def mock_screenshot() -> ScreenshotResult:
        """Mock screenshot function that returns results in sequence"""
        # Get current context and advance sequence
        context = contexts[current_context["index"]]
        current_context["index"] = (current_context["index"] + 1) % len(contexts)
        
        # Get image metadata
        image_path = mock_screenshots[context]
        with Image.open(image_path) as img:
            width, height = img.size
            
        metadata = ScreenshotMetadata(
            timestamp=datetime.now(),
            path=str(image_path),
            resolution=(width, height),
            description=f"Mock {context} screenshot"
        )
        
        return ScreenshotResult(
            metadata=metadata,
            detected=get_mock_elements(context),
            validation_status=ValidationStatus.SUCCESS,
            analysis_complete=True
        )
    
    return mock_screenshot