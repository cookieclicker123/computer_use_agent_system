import pytest
from pathlib import Path
from PIL import Image
from src.data_model import (
    ScreenshotResult, DetectedElements, DetectedElement,
    UIElement, UIElementType, ValidationStatus,
    MouseAction, KeyboardAction
)
from mocks.mock_screenshot_agent import create_screenshot_agent

@pytest.fixture
def screenshot_fn():
    return create_screenshot_agent(mock=True)

def test_screenshot_sequence(screenshot_fn):
    """Test that screenshots follow the correct sequence: vscode -> desktop -> chrome"""
    contexts = ["vscode", "desktop", "chrome"]
    
    for expected_context in contexts:
        result = screenshot_fn()
        assert isinstance(result, ScreenshotResult)
        assert expected_context in result.metadata.description.lower()
        assert result.analysis_complete is True

def test_detected_elements_structure(screenshot_fn):
    """Test that detected elements follow our data model structure"""
    result = screenshot_fn()
    
    # Check DetectedElements container
    assert isinstance(result.detected, DetectedElements)
    assert result.detected.total_count > 0
    assert 0 <= result.detected.highest_confidence <= 1.0
    
    # Check individual elements
    for element in result.detected.elements:
        assert isinstance(element, DetectedElement)
        assert isinstance(element.element, UIElement)
        assert 0 <= element.confidence <= 1.0
        assert len(element.possible_actions) > 0
        
        # Check bounding box format
        if element.bounding_box:
            x, y, w, h = element.bounding_box
            assert all(isinstance(v, int) for v in (x, y, w, h))
            assert all(v >= 0 for v in (w, h))

def test_context_specific_elements(screenshot_fn):
    """Test that each context has appropriate UI elements"""
    # VSCode context
    result = screenshot_fn()
    assert "vscode" in result.metadata.description.lower()
    vscode_types = {e.element.element_type for e in result.detected.elements}
    assert UIElementType.TERMINAL in vscode_types
    
    # Desktop context
    result = screenshot_fn()
    assert "desktop" in result.metadata.description.lower()
    desktop_types = {e.element.element_type for e in result.detected.elements}
    assert UIElementType.ICON in desktop_types
    
    # Chrome context
    result = screenshot_fn()
    assert "chrome" in result.metadata.description.lower()
    chrome_types = {e.element.element_type for e in result.detected.elements}
    assert UIElementType.SEARCH_BAR in chrome_types

def test_action_mappings(screenshot_fn):
    """Test that elements have appropriate possible actions"""
    result = screenshot_fn()
    
    for element in result.detected.elements:
        if element.element.element_type == UIElementType.SEARCH_BAR:
            assert KeyboardAction.TYPE in element.possible_actions
            assert MouseAction.LEFT_CLICK in element.possible_actions
        elif element.element.element_type == UIElementType.BUTTON:
            assert MouseAction.LEFT_CLICK in element.possible_actions
        elif element.element.element_type == UIElementType.ICON:
            assert MouseAction.DOUBLE_CLICK in element.possible_actions

def test_metadata_validity(screenshot_fn):
    """Test screenshot metadata structure and validity"""
    result = screenshot_fn()
    
    assert result.metadata.timestamp is not None
    assert Path(result.metadata.path).exists()
    assert len(result.metadata.resolution) == 2
    assert all(v > 0 for v in result.metadata.resolution)
    
    # Verify image can be opened
    with Image.open(result.metadata.path) as img:
        assert img.size == result.metadata.resolution

def test_confidence_calculations(screenshot_fn):
    """Test confidence scores and highest confidence calculation"""
    result = screenshot_fn()
    
    # Verify highest_confidence calculation
    max_confidence = max(e.confidence for e in result.detected.elements)
    assert result.detected.highest_confidence == max_confidence
    
    # Verify all confidences are valid
    for element in result.detected.elements:
        assert 0 <= element.confidence <= 1.0

def test_validation_status(screenshot_fn):
    """Test that validation status is properly set"""
    result = screenshot_fn()
    assert result.validation_status == ValidationStatus.SUCCESS
    assert result.analysis_complete is True

def test_error_handling(monkeypatch):
    """Test error handling for missing fixtures"""
    # Patch Path.exists to return False to simulate missing files
    def mock_exists(self):
        return False
    
    monkeypatch.setattr(Path, "exists", mock_exists)
    
    # Now this should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        create_screenshot_agent(mock=True)

def test_sequence_wrapping(screenshot_fn):
    """Test that sequence properly wraps around"""
    # Go through sequence twice
    contexts = ["vscode", "desktop", "chrome"] * 2
    
    for expected_context in contexts:
        result = screenshot_fn()
        assert expected_context in result.metadata.description.lower() 