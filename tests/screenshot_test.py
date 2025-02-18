import pyautogui
from PIL import Image
from datetime import datetime

def take_screenshot():
    try:
        # Take screenshot
        screenshot = pyautogui.screenshot()
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./tests/fixtures/screenshot_{timestamp}.png"
        
        # Save to root directory
        screenshot.save(filename)
        print(f"Screenshot saved as {filename}")
        
        return filename
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None

if __name__ == "__main__":
    # Ensure we have permissions
    print("Please grant screen recording permissions if prompted...")
    print("Taking screenshot in 3 seconds...")
    pyautogui.sleep(3)
    
    filename = take_screenshot()
    
    if filename:
        # Open the image to verify
        Image.open(filename).show() 