from typing import Dict
from src.data_model import (
    TaskPlan, Task, TaskAction, UIElement, 
    MouseAction, UIElementType, 
    taskPlannerFn
)

def create_task_planner(mock: bool = True) -> taskPlannerFn:
    """Factory function that creates and returns a task planner function"""
    
    def create_google_search_plan(query: str) -> TaskPlan:
        return TaskPlan(
            goal=f"Search Google for '{query}'",
            tasks=[
                Task(
                    task_id="locate_search",
                    description="Find Google search bar",
                    actions=[
                        TaskAction(
                            action_type=MouseAction.LEFT_CLICK,
                            target_element=UIElement(
                                element_type=UIElementType.TEXT_INPUT,
                                description="Google search bar"
                            )
                        )
                    ]
                )
            ]
        )
    
    def mock_planner(goal: str, context: Dict = None) -> TaskPlan:
        if "google search" in goal.lower():
            return create_google_search_plan(goal)
        raise ValueError(f"No mock plan available for goal: {goal}")
    
    return mock_planner
    
    