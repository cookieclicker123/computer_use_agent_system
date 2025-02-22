import logging
from pathlib import Path
from dotenv import load_dotenv
from src.task_planner import create_task_planner
from src.screenshot_vision_agent import create_screenshot_agent
from src.vision_output_processor import create_vision_processor
from src.data_model import TaskPlan
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table
import openai
import os

# Configure rich console and logging
console = Console()

# Load environment variables and set up paths
ROOT_DIR = Path(__file__).parent
FIXTURES_PATH = ROOT_DIR / "tests" / "fixtures" / "test_screenshots"
load_dotenv(ROOT_DIR / ".env")

def display_task_plan(plan: TaskPlan):
    """Display task plan in a tree structure"""
    tree = Tree(f"[bold blue]Task Plan: {plan.goal}")
    for task in plan.tasks:
        task_node = tree.add(f"[bold green]Task: {task.description}")
        for action in task.actions:
            action_node = task_node.add(f"[yellow]Action: {action.action_type}")
            target = action.target_element
            action_node.add(f"Target: {target.element_type} ({target.description})")
    console.print(tree)

def display_detected_elements(screenshot_results):
    """Display the detected UI elements and their possible actions from screenshots"""
    console.print("\n[bold blue]Detected UI Elements:[/]")
    
    if not screenshot_results:
        console.print("[yellow]No elements detected[/]")
        return
        
    # Create a table for the elements
    elements_table = Table(show_header=True, header_style="bold magenta")
    elements_table.add_column("Screenshot")
    elements_table.add_column("Element Count", justify="center")
    elements_table.add_column("Highest Confidence", justify="center")
    elements_table.add_column("Elements")
    
    # Create a table for the actions
    actions_table = Table(show_header=True, header_style="bold cyan")
    actions_table.add_column("Screenshot")
    actions_table.add_column("Element")
    actions_table.add_column("Confidence", justify="center")
    actions_table.add_column("Possible Actions")
    
    # Handle each screenshot result
    for result in screenshot_results:
        filename = Path(result.metadata.path).name if result.metadata else "Unknown"
        
        # Extract element types for the elements table
        element_types = [
            e.element.element_type 
            for e in result.detected.elements
        ]
        elements_info = ", ".join(element_types) if element_types else "No elements"
        
        elements_table.add_row(
            filename,
            str(len(result.detected.elements)),
            f"{result.detected.highest_confidence:.2f}",
            elements_info
        )
        
        # Add detailed actions for each element
        for element in result.detected.elements:
            actions = [str(action) for action in element.possible_actions]
            actions_info = ", ".join(actions) if actions else "No actions"
            
            actions_table.add_row(
                filename,
                f"{element.element.element_type} ({element.element.description})",
                f"{element.confidence:.2f}",
                actions_info
            )
    
    console.print(elements_table)
    console.print("\n[bold blue]Available Actions:[/]")
    console.print(actions_table)
    console.print()

def main():
    console.print("[bold blue]Computer Use Agent - Task Planning with Vision[/]")
    
    # Debug API keys
    openai_api_key = os.getenv("OPENAI_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    print("API Key Status:")
    print(f"OpenAI API Key present: {bool(openai_api_key)}")
    print(f"OpenAI API Key length: {len(openai_api_key) if openai_api_key else 0}")
    print(f"Groq API Key present: {bool(groq_api_key)}")
    
    try:
        # Test OpenAI client creation
        print("Testing OpenAI client creation...")
        test_client = openai.OpenAI(api_key=openai_api_key)
        print("OpenAI client created successfully")
        
        # Create components
        print("Creating task planner...")
        task_planner = create_task_planner(api_key=openai_api_key)
        print("Task planner created")
        
        screenshot_fn = create_screenshot_agent(use_vision=True, api_key=groq_api_key)
        vision_processor = create_vision_processor()
        
        # Create client for vision processor
        openai_client = openai.OpenAI(api_key=openai_api_key)
        
    except Exception as e:
        print(f"Setup error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return

    screenshots = ["vscode.png", "desktop.png", "google_chrome.png"]
    
    while True:
        try:
            query = console.input("\n[bold green]What would you like to do?[/] ")
            if query.lower() == 'exit':
                break
            
            # 1. Get task plan
            console.print("\n[bold yellow]Getting task plan...[/]")
            try:
                task_plan = task_planner(query)
                console.print("\n[bold green]✓ Task plan created[/]")
                display_task_plan(task_plan)
            except Exception as e:
                print(f"Task planning failed: {str(e)}")
                continue
            
            # 2. Analyze screenshots
            vision_outputs = []
            console.print("\n[bold yellow]Analyzing screenshots...[/]")
            
            for screenshot in screenshots:
                screenshot_path = FIXTURES_PATH / screenshot
                try:
                    console.print(f"Processing {screenshot}...")
                    screenshot_result = screenshot_fn(str(screenshot_path))
                    vision_outputs.append(screenshot_result)
                    
                    if hasattr(screenshot_result.detected, 'raw_output'):
                        console.print(Panel(
                            screenshot_result.detected.raw_output,
                            title=f"Vision Output - {screenshot}",
                            border_style="blue"
                        ))
                    else:
                        console.print(f"[red]No raw output for {screenshot}[/]")
                        
                except Exception as e:
                    print(f"Vision analysis failed for {screenshot}: {str(e)}")
                    continue
            
            if not vision_outputs:
                print("No vision outputs to process")
                continue
                
            # 3. Process vision outputs
            console.print("\n[bold yellow]Processing vision outputs...[/]")
            try:
                grounded_elements = vision_processor(
                    vision_outputs=vision_outputs,
                    task_plan=task_plan,
                    client=openai_client
                )
                
                console.print("\n[bold magenta]Grounded Elements:[/]")
                display_detected_elements(vision_outputs)
                
            except Exception as e:
                print(f"Vision processing failed: {str(e)}")
                print(f"Error type: {type(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                continue

        except Exception as e:
            print(f"Main loop error: {str(e)}")
            print(f"Error type: {type(e)}")
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Exiting...[/]")
    except Exception as e:
        print(f"Application error: {e}") 