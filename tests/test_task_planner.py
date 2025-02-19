import pytest
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from src.data_model import (
    TaskPlan, MouseAction, KeyboardAction, 
    SystemAction, UIElementType, ValidationStatus
)
from src.task_planner import create_task_planner

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env", verbose=True)

@pytest.fixture
def api_key():
    key = os.getenv("OPENAI_API_KEY")
    print(f"\nChecking for API key...")
    print(f"Found key: {'Yes' if key else 'No'}")
    print(f".env file location: {ROOT_DIR / '.env'}")
    if not key:
        raise pytest.UsageError(
            "\nOPENAI_API_KEY not found in .env file!"
            f"\nExpected .env file at: {ROOT_DIR / '.env'}"
            "\nPlease create a .env file with:"
            "\nOPENAI_API_KEY='your-api-key'"
        )
    return key

def test_api_connection(api_key):
    """Verify OpenAI API connection and basic functionality"""
    print(f"\nTesting API connection with key: {api_key[:6]}...")
    client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        assert response is not None
        assert response.choices[0].message.content is not None
        print(f"API Test Response: {response.choices[0].message.content}")
    except Exception as e:
        pytest.fail(f"API connection failed: {str(e)}")

@pytest.fixture
def task_planner(api_key):
    return create_task_planner(api_key)

def test_basic_task_plan_structure(task_planner):
    """Test that a simple query generates a valid task plan structure"""
    plan = task_planner("what is a neural network?")
    print(f"\nGenerated Task Plan:\n{plan.model_dump_json(indent=2)}")
    
    # Verify basic structure
    assert isinstance(plan, TaskPlan)
    assert "neural network" in plan.goal.lower()
    assert len(plan.tasks) > 0
    assert plan.current_task_index == 0
    assert plan.status == ValidationStatus.PENDING

def test_task_sequence_logic(task_planner):
    """Test that tasks are in logical sequence with correct dependencies"""
    plan = task_planner("what is a neural network?")
    print(f"\nTask Sequence:\n")
    for task in plan.tasks:
        print(f"Task: {task.task_id}")
        print(f"Dependencies: {task.dependencies}")
        print(f"Actions: {[a.action_type for a in task.actions]}\n")
    
    # Find search task
    search_task = next(t for t in plan.tasks if "search" in t.task_id.lower())
    # Should depend on browser being ready
    assert any("chrome" in dep.lower() for dep in search_task.dependencies)

def test_action_validation_structure(task_planner):
    """Test that each action has proper validation setup"""
    plan = task_planner("what is a neural network?")
    
    print("\nValidation Structure:")
    for task in plan.tasks:
        print(f"\nTask: {task.task_id}")
        for action in task.actions:
            print(f"Action: {action.action_type}")
            print(f"Validation: {action.validation_result}")
            print(f"Retry Strategy: {action.retry_strategy}")
    
    # Check validation setup
    for task in plan.tasks:
        for action in task.actions:
            assert action.validation_result is not None
            assert action.validation_result.status == ValidationStatus.PENDING
            assert action.validation_result.max_retries > 0
            assert action.retry_strategy is not None
            assert "max_attempts" in action.retry_strategy
            assert "delay_between_attempts" in action.retry_strategy

def test_enum_value_correctness(task_planner):
    """Test that all enum values match our defined values exactly"""
    plan = task_planner("what is a neural network?")
    
    for task in plan.tasks:
        for action in task.actions:
            if isinstance(action.action_type, MouseAction):
                assert action.action_type.value in [a.value for a in MouseAction]
            elif isinstance(action.action_type, KeyboardAction):
                assert action.action_type.value in [a.value for a in KeyboardAction]
            elif isinstance(action.action_type, SystemAction):
                assert action.action_type.value in [a.value for a in SystemAction]
            
            assert action.target_element.element_type.value in [t.value for t in UIElementType]
            assert action.validation_result.status.value in [s.value for s in ValidationStatus]

def test_user_query_incorporation(task_planner):
    """Test that the user's query is properly incorporated into the task plan"""
    query = "what is a neural network?"
    plan = task_planner(query)
    
    # Check query appears in goal
    assert query.lower().replace("?", "") in plan.goal.lower()
    
    # Check query appears in search action
    search_task = next(t for t in plan.tasks if "search" in t.task_id.lower())
    type_action = next(a for a in search_task.actions if a.action_type == KeyboardAction.TYPE)
    assert query.lower().replace("?", "") in type_action.input_data.lower()

def test_retry_strategy_configuration(task_planner):
    """Test that retry strategies are properly configured"""
    plan = task_planner("what is a neural network?")
    
    for task in plan.tasks:
        for action in task.actions:
            assert "max_attempts" in action.retry_strategy
            assert "delay_between_attempts" in action.retry_strategy
            assert isinstance(action.retry_strategy["max_attempts"], int)
            assert isinstance(action.retry_strategy["delay_between_attempts"], float)
            assert action.retry_strategy["max_attempts"] > 0
            assert action.retry_strategy["delay_between_attempts"] > 0

def test_confidence_thresholds(task_planner):
    """Test that confidence thresholds are appropriate for different UI elements"""
    plan = task_planner("what is a neural network?")
    
    for task in plan.tasks:
        for action in task.actions:
            assert 0 < action.target_element.confidence_required <= 1
            # Critical actions should require higher confidence
            if action.target_element.element_type in [UIElementType.BUTTON, UIElementType.SEARCH_BAR]:
                assert action.target_element.confidence_required >= 0.8


