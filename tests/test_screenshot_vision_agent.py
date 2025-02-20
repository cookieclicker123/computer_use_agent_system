import pytest
from pathlib import Path
import os
from PIL import Image
from src.data_model import (
    ScreenshotResult, DetectedElements, DetectedElement,
    UIElement, UIElementType, ValidationStatus,
    MouseAction, KeyboardAction
)
from src.screenshot_vision_agent import create_screenshot_agent

@pytest.fixture
def vision_screenshot_fn():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        pytest.skip("GROQ_API_KEY not found in environment")
    return create_screenshot_agent(use_vision=True, api_key=api_key)

def test_screenshot_sequence(vision_screenshot_fn):
    """Test vision model on full screenshot sequence with detailed debugging"""
    fixtures_path = Path(__file__).parent / "fixtures" / "test_screenshots"
    screenshots = [
        ("vscode.png", {UIElementType.WINDOW, UIElementType.TERMINAL}),
        ("desktop.png", {UIElementType.ICON, UIElementType.TASKBAR}),
        ("google_chrome.png", {UIElementType.SEARCH_BAR, UIElementType.BUTTON})
    ]
    
    for filename, expected_types in screenshots:
        print(f"\n=== Testing {filename} ===")
        
        # Stage 1: Get result
        result = vision_screenshot_fn(str(fixtures_path / filename))
        print(f"Got result with {len(result.detected.elements)} elements")
        
        # Stage 2: Check detected types
        detected_types = {e.element.element_type for e in result.detected.elements}
        print(f"Detected types: {detected_types}")
        print(f"Expected types: {expected_types}")
        
        # Stage 3: Check raw elements
        print("\nRaw elements:")
        for element in result.detected.elements:
            print(f"- Type: {element.element.element_type}")
            print(f"  Description: {element.element.description}")
            print(f"  Confidence: {element.confidence}")
            print(f"  Actions: {element.possible_actions}")
        
        # Now run assertions
        assert isinstance(result, ScreenshotResult), "Result type check failed"
        assert result.analysis_complete is True, "Analysis complete check failed"
        
        matching_types = detected_types.intersection(expected_types)
        print(f"\nMatching types: {matching_types}")
        
        assert any(t in detected_types for t in expected_types), \
            f"Expected to find at least one of {expected_types} in {filename}, got {detected_types}"

def test_vision_model_structure(vision_screenshot_fn):
    """Test that vision model output matches our data model structure"""
    fixtures_path = Path(__file__).parent / "fixtures" / "test_screenshots"
    test_image = fixtures_path / "google_chrome.png"
    
    result = vision_screenshot_fn(str(test_image))
    assert isinstance(result, ScreenshotResult)
    assert result.analysis_complete is True
    
    # Check DetectedElements container
    assert isinstance(result.detected, DetectedElements)
    assert result.detected.total_count > 0
    assert 0 <= result.detected.highest_confidence <= 1.0
    
    # Check individual elements
    for element in result.detected.elements:
        assert isinstance(element, DetectedElement)
        assert isinstance(element.element, UIElement)
        assert element.element.element_type in UIElementType
        assert 0 <= element.confidence <= 1.0
        assert len(element.possible_actions) > 0
        
        # Check bounding box format if present
        if element.bounding_box:
            x, y, w, h = element.bounding_box
            assert all(isinstance(v, int) for v in (x, y, w, h))
            assert all(v >= 0 for v in (w, h))

def test_context_specific_detection(vision_screenshot_fn):
    """Test that model detects appropriate elements for different contexts"""
    fixtures_path = Path(__file__).parent / "fixtures" / "test_screenshots"
    
    # Test Chrome context
    chrome_result = vision_screenshot_fn(str(fixtures_path / "google_chrome.png"))
    chrome_types = {e.element.element_type for e in chrome_result.detected.elements}
    assert UIElementType.SEARCH_BAR in chrome_types
    
    # Test VSCode context
    vscode_result = vision_screenshot_fn(str(fixtures_path / "vscode.png"))
    vscode_types = {e.element.element_type for e in vscode_result.detected.elements}
    assert UIElementType.TERMINAL in vscode_types or UIElementType.WINDOW in vscode_types

def test_action_inference(vision_screenshot_fn):
    """Test that model infers appropriate actions for elements"""
    fixtures_path = Path(__file__).parent / "fixtures" / "test_screenshots"
    result = vision_screenshot_fn(str(fixtures_path / "google_chrome.png"))
    
    for element in result.detected.elements:
        if element.element.element_type == UIElementType.SEARCH_BAR:
            assert KeyboardAction.TYPE in element.possible_actions
            assert MouseAction.LEFT_CLICK in element.possible_actions
        elif element.element.element_type == UIElementType.BUTTON:
            assert MouseAction.LEFT_CLICK in element.possible_actions

def test_confidence_calculations(vision_screenshot_fn):
    """Test confidence scores and calculations"""
    fixtures_path = Path(__file__).parent / "fixtures" / "test_screenshots"
    result = vision_screenshot_fn(str(fixtures_path / "google_chrome.png"))
    
    # Verify highest_confidence calculation
    max_confidence = max(e.confidence for e in result.detected.elements)
    assert result.detected.highest_confidence == max_confidence
    
    # Verify all confidences are valid
    for element in result.detected.elements:
        assert 0 <= element.confidence <= 1.0

def test_metadata_validity(vision_screenshot_fn):
    """Test screenshot metadata structure"""
    fixtures_path = Path(__file__).parent / "fixtures" / "test_screenshots"
    test_image = fixtures_path / "google_chrome.png"
    result = vision_screenshot_fn(str(test_image))
    
    assert result.metadata.timestamp is not None
    assert Path(result.metadata.path).exists()
    assert len(result.metadata.resolution) == 2
    assert all(v > 0 for v in result.metadata.resolution)
    
    with Image.open(result.metadata.path) as img:
        assert img.size == result.metadata.resolution

def test_error_handling():
    """Test error handling for invalid inputs"""
    with pytest.raises(Exception):
        screenshot_fn = create_screenshot_agent(use_vision=True, api_key="invalid")
        screenshot_fn("nonexistent.png")

def test_fallback_to_mock():
    """Test fallback to mock when vision is disabled"""
    screenshot_fn = create_screenshot_agent(use_vision=False)
    result = screenshot_fn("any_path.png")
    assert isinstance(result, ScreenshotResult)
    assert result.analysis_complete is True 