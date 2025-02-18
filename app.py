import logging
from pathlib import Path
from dotenv import load_dotenv
from src.task_planner import create_task_planner
from src.data_model import TaskPlan, ValidationStatus
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint

# Configure rich console
console = Console()

# Configure logging with rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env", verbose=True)

def get_status_color(status: ValidationStatus) -> str:
    """Get color for status display"""
    return {
        ValidationStatus.PENDING: "yellow",
        ValidationStatus.SUCCESS: "green",
        ValidationStatus.FAILED: "red",
        ValidationStatus.RETRY: "yellow"
    }.get(status, "white")

def display_task_plan(plan: TaskPlan):
    """Pretty print the task plan with rich formatting"""
    
    # Create main tree
    tree = Tree(f"[bold blue]Task Plan: {plan.goal}")
    
    # Add tasks to tree
    for i, task in enumerate(plan.tasks, 1):
        # Create task node
        task_color = get_status_color(task.validation_status)
        task_node = tree.add(
            f"[bold {task_color}]Task {i}: {task.task_id}"
        )
        
        # Add task details
        task_node.add(f"[italic]Description: {task.description}")
        if task.dependencies:
            task_node.add(f"[yellow]Dependencies: {', '.join(task.dependencies)}")
        
        # Add actions
        action_node = task_node.add("[bold cyan]Actions:")
        
        for j, action in enumerate(task.actions, 1):
            # Format action details
            status_color = get_status_color(action.validation_result.status)
            action_details = [
                f"Type: {action.action_type}",
                f"Target: {action.target_element.element_type} ({action.target_element.description})",
                f"Confidence: {action.target_element.confidence_required:.1%}"
            ]
            
            if hasattr(action, 'input_data') and action.input_data:
                action_details.append(f"Input: {action.input_data}")
            
            action_node.add(
                f"[{status_color}]{j}. " + " | ".join(action_details)
            )
    
    # Print the tree in a panel
    console.print(Panel(
        tree,
        title="[bold]Generated Task Plan",
        border_style="blue"
    ))
    
    # Show execution status
    console.print(Panel(
        f"[bold]Status: [bold {get_status_color(plan.status)}]{plan.status}[/]\n"
        f"Current Task: {plan.current_task_index + 1}/{len(plan.tasks)}",
        title="[bold]Execution Status",
        border_style="green"
    ))

def main():
    console.print(Panel(
        "[bold blue]Computer Use Agent - Task Planning Demo[/]\n"
        "[italic]Type 'exit' to quit[/]",
        border_style="bold"
    ))
    
    # Create task planner
    task_planner = create_task_planner()
    
    while True:
        try:
            # Get user input
            query = console.input("\n[bold green]What would you like to know?[/] ")
            if query.lower() == 'exit':
                break
                
            console.print("\n[bold yellow]Generating task plan...[/]")
            logger.info(f"Processing query: {query}")
            
            # Generate task plan
            plan = task_planner(query)
            
            # Display the plan
            display_task_plan(plan)
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            console.print(f"\n[bold red]Error:[/] {str(e)}")
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Exiting...[/]")
    except Exception as e:
        logger.error(f"Application error: {e}")
        console.print(f"\n[bold red]Application error:[/] {str(e)}") 