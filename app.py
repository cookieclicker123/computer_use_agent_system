import logging
from pathlib import Path
from dotenv import load_dotenv
from src.task_planner import create_task_planner
from src.screenshot_vision_agent import create_screenshot_agent
from src.vision_output_processor import create_vision_processor
from src.data_model import TaskPlan, ValidationStatus
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table
import groq
import openai
import os

# Configure rich console and logging
console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Display the detected UI elements from screenshots"""
    console.print("\n[bold blue]Detected UI Elements:[/]")
    
    if not screenshot_results:
        console.print("[yellow]No elements detected[/]")
        return
        
    # Create a table for the results
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Screenshot")
    table.add_column("Elements")
    
    # Handle each screenshot result
    for result in screenshot_results:
        filename = Path(result.metadata.path).name if result.metadata else "Unknown"
        
        # Extract element types from detected elements
        element_types = [
            e.element.element_type 
            for e in result.detected.elements
        ]
        elements_info = ", ".join(element_types) if element_types else "No elements"
        
        table.add_row(
            filename,
            elements_info
        )
    
    console.print(table)
    console.print()

def main():
    console.print("[bold blue]Computer Use Agent - Task Planning with Vision[/]")
    
    # Debug API keys
    openai_api_key = os.getenv("OPENAI_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    logger.info("API Key Status:")
    logger.info(f"OpenAI API Key present: {bool(openai_api_key)}")
    logger.info(f"OpenAI API Key length: {len(openai_api_key) if openai_api_key else 0}")
    logger.info(f"Groq API Key present: {bool(groq_api_key)}")
    
    try:
        # Test OpenAI client creation
        logger.info("Testing OpenAI client creation...")
        test_client = openai.OpenAI(api_key=openai_api_key)
        logger.info("OpenAI client created successfully")
        
        # Create components
        logger.info("Creating task planner...")
        task_planner = create_task_planner(api_key=openai_api_key)
        logger.info("Task planner created")
        
        screenshot_fn = create_screenshot_agent(use_vision=True, api_key=groq_api_key)
        vision_processor = create_vision_processor()
        
        # Create client for vision processor
        openai_client = openai.OpenAI(api_key=openai_api_key)
        
    except Exception as e:
        logger.error(f"Setup error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
                logger.error(f"Task planning failed: {str(e)}")
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
                    logger.error(f"Vision analysis failed for {screenshot}: {str(e)}")
                    continue
            
            if not vision_outputs:
                logger.error("No vision outputs to process")
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
                logger.error(f"Vision processing failed: {str(e)}")
                logger.error(f"Error type: {type(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue

        except Exception as e:
            logger.error(f"Main loop error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Exiting...[/]")
    except Exception as e:
        logger.error(f"Application error: {e}") 