from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal, Tuple, Callable, Dict
from enum import Enum

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
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"

ActionType = Union[MouseAction, KeyboardAction, SystemAction]

class UIElementType(Enum):
    BUTTON = "button"
    TEXT_INPUT = "text_input"
    LINK = "link"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    ICON = "icon"
    MENU_ITEM = "menu_item"
    TAB = "tab"
    SLIDER = "slider"
    SCROLLBAR = "scrollbar"
    GENERIC = "generic"
    SEARCH_BAR = "search_bar"

class UIElement(BaseModel):
    element_type: UIElementType
    description: str
    expected_location: Optional[Tuple[float, float]] = None
    confidence_required: float = Field(default=0.6, ge=0, le=1.0)
    context: Optional[str] = None

class ValidationResult(BaseModel):
    status: ValidationStatus
    message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class TaskAction(BaseModel):
    action_type: ActionType
    target_element: UIElement
    input_data: Optional[str] = None
    validation_result: Optional[ValidationResult] = None
    retry_strategy: dict = Field(
        default_factory=lambda: {
            "max_attempts": 3,
            "delay_between_attempts": 1.0,
            "fallback_action": None
        }
    )

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