from pathlib import Path
from datetime import datetime
from src.data_model import (
    DetectedElements, DetectedElement, UIElement, 
    UIElementType, MouseAction, KeyboardAction,
    ScreenshotResult, ScreenshotMetadata
)

def test_screenshot_element_grouping():
    """Test that elements are correctly grouped per screenshot"""
    
    fixtures_path = Path(__file__).parent / "fixtures" / "test_screenshots"
    
    # Create sample screenshots with known elements
    screenshots = [
        ScreenshotResult(
            metadata=ScreenshotMetadata(
                path=str(fixtures_path / "vscode.png"),
                timestamp=datetime.now(),
                resolution=(1920, 1080),
                description="VSCode IDE window with terminal"
            ),
            detected=DetectedElements(
                elements=[
                    DetectedElement(
                        element=UIElement(
                            element_type=UIElementType.WINDOW,
                            description="VSCode Window"
                        ),
                        confidence=0.95,
                        possible_actions=[MouseAction.LEFT_CLICK]
                    ),
                    DetectedElement(
                        element=UIElement(
                            element_type=UIElementType.TERMINAL,
                            description="Integrated Terminal"
                        ),
                        confidence=0.90,
                        possible_actions=[KeyboardAction.TYPE]
                    )
                ],
                total_count=2,
                highest_confidence=0.95
            )
        ),
        ScreenshotResult(
            metadata=ScreenshotMetadata(
                path=str(fixtures_path / "google_chrome.png"),
                timestamp=datetime.now(),
                resolution=(1920, 1080),
                description="Google Chrome browser window"
            ),
            detected=DetectedElements(
                elements=[
                    DetectedElement(
                        element=UIElement(
                            element_type=UIElementType.SEARCH_BAR,
                            description="Google Search"
                        ),
                        confidence=0.95,
                        possible_actions=[MouseAction.LEFT_CLICK, KeyboardAction.TYPE]
                    ),
                    DetectedElement(
                        element=UIElement(
                            element_type=UIElementType.BUTTON,
                            description="Search Button"
                        ),
                        confidence=0.90,
                        possible_actions=[MouseAction.LEFT_CLICK]
                    )
                ],
                total_count=2,
                highest_confidence=0.95
            )
        )
    ]
    
    # Verify each screenshot has its own elements
    assert len(screenshots) == 2
    
    # Check VSCode screenshot
    vscode = screenshots[0]
    assert Path(vscode.metadata.path).name == "vscode.png"
    assert len(vscode.detected.elements) == 2
    assert vscode.detected.elements[0].element.element_type == UIElementType.WINDOW
    assert vscode.detected.elements[1].element.element_type == UIElementType.TERMINAL
    
    # Check Chrome screenshot
    chrome = screenshots[1]
    assert Path(chrome.metadata.path).name == "google_chrome.png"
    assert len(chrome.detected.elements) == 2
    assert chrome.detected.elements[0].element.element_type == UIElementType.SEARCH_BAR
    assert chrome.detected.elements[1].element.element_type == UIElementType.BUTTON
    
    # Verify elements stay with their screenshots
    for screenshot in screenshots:
        assert hasattr(screenshot.detected, 'elements')
        assert len(screenshot.detected.elements) > 0
        assert screenshot.detected.total_count == len(screenshot.detected.elements) 