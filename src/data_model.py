from pydantic import BaseModel, Field
from typing import List, Optional, Union, Tuple, Callable, Dict
from enum import Enum
from datetime import datetime

class MouseAction(Enum):
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    DRAG = "drag"
    DROP = "drop"
    HOVER = "hover"

class KeyboardAction(Enum):
    TYPE = "type"
    HOTKEY = "hotkey"
    PRESS = "press"
    RELEASE = "release"
    CTRL_LEFT = "ctrl_left"
    ALT_TAB = "alt_tab"
    WINDOWS = "windows"
    ESC = "escape"

class SystemAction(Enum):
    WAIT = "wait"
    VERIFY = "verify"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"

class ValidationStatus(Enum):
    """Status of validation checks"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"

ActionType = Union[MouseAction, KeyboardAction, SystemAction]

class UIElementType(str, Enum):
    WINDOW = "window"
    TERMINAL = "terminal"
    ICON = "icon"
    TASKBAR = "taskbar"
    SEARCH_BAR = "search_bar"
    TEXT_INPUT = "text_input"     # Functionally same as SEARCH_BAR
    BUTTON = "button"
    MENU_ITEM = "menu_item"       # Functionally similar to ICON/TASKBAR items
    MENU_BAR = "menu_bar"         # Functionally similar to TASKBAR

class UIElement(BaseModel):
    element_type: UIElementType
    description: str
    expected_location: Optional[Tuple[float, float]] = None
    confidence_required: float = Field(default=0.6, ge=0, le=1.0)
    context: Optional[str] = None

class ValidationResult(BaseModel):
    """Result of validation checks"""
    status: ValidationStatus = ValidationStatus.PENDING
    message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class ScreenshotMetadata(BaseModel):
    """Metadata for screenshot capture and analysis"""
    timestamp: datetime
    path: str
    resolution: tuple[int, int]
    description: Optional[str] = None

class DetectedElement(BaseModel):
    """An element detected in the screenshot with its possible actions"""
    element: UIElement
    confidence: float
    possible_actions: list[ActionType] = []
    bounding_box: Optional[tuple[int, int, int, int]] = None

class DetectedElements(BaseModel):
    """Container for detected UI elements from a screenshot"""
    elements: List[DetectedElement] = []
    total_count: int = 0
    highest_confidence: float = 0.0
    raw_output: Optional[str] = None

class ScreenshotResult(BaseModel):
    """Result of screenshot analysis with detected elements and possible actions"""
    metadata: ScreenshotMetadata
    detected: DetectedElements = DetectedElements()
    validation_status: ValidationStatus = ValidationStatus.PENDING
    analysis_complete: bool = False

class ScreenshotAction(BaseModel):
    """Action to take screenshot and analyze results"""
    chosen_element: Optional[DetectedElement] = None
    confidence_threshold: float = 0.8
    automation_ready: bool = False

class TaskAction(BaseModel):
    """Represents a single action within a task"""
    action_type: ActionType
    target_element: UIElement
    input_data: Optional[str] = None
    screenshot_before: Optional[ScreenshotResult] = None
    screenshot_after: Optional[ScreenshotResult] = None
    validation_result: ValidationResult = ValidationResult(
        status=ValidationStatus.PENDING,
        message=None,
        retry_count=0,
        max_retries=3
    )
    retry_strategy: Dict = {
        "max_attempts": 3,
        "delay_between_attempts": 1.0
    }

class Task(BaseModel):
    task_id: str
    description: str
    actions: List[TaskAction]
    dependencies: List[str] = Field(default_factory=list)
    validation_status: ValidationStatus = ValidationStatus.PENDING

class TaskPlan(BaseModel):
    goal: str
    tasks: List[Task]
    current_task_index: int = 0
    status: ValidationStatus = ValidationStatus.PENDING

taskPlannerFn = Callable[[str, Dict], TaskPlan]

# Screenshot function type signature
ScreenshotFn = Callable[[], ScreenshotResult]