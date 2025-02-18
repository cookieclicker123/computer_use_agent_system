import pytest
from src.data_model import (
    TaskPlan, MouseAction, UIElementType
)
from mocks.mock_llm import create_task_planner

@pytest.fixture
def task_planner():
    return create_task_planner(mock=True)

def test_basic_google_search_plan(task_planner):
    plan = task_planner("google search for cats")
    assert isinstance(plan, TaskPlan)
    assert plan.status == "pending"
    assert len(plan.tasks) > 0
    assert plan.tasks[0].task_id == "locate_search"

def test_invalid_goal_raises_error(task_planner):
    with pytest.raises(ValueError) as exc_info:
        task_planner("something we haven't mocked")
    assert "No mock plan available" in str(exc_info.value)

def test_task_plan_validation():
    planner = create_task_planner(mock=True)
    plan = planner("google search for dogs")
    
    # Validate task structure
    first_task = plan.tasks[0]
    first_action = first_task.actions[0]
    
    assert first_action.action_type == MouseAction.LEFT_CLICK
    assert first_action.target_element.element_type == UIElementType.TEXT_INPUT
    assert first_action.target_element.confidence_required >= 0.0
    assert first_action.target_element.confidence_required <= 1.0

def test_task_dependencies():
    planner = create_task_planner(mock=True)
    plan = planner("google search for cats")
    
    # Ensure tasks are ordered correctly
    search_tasks = [t for t in plan.tasks if "search" in t.description.lower()]
    assert len(search_tasks) > 0
    
    # Validate dependency chain
    for task in plan.tasks[1:]:  # Skip first task
        assert len(task.dependencies) > 0