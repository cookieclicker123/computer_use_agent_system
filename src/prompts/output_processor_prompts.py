CONDENSE_PROMPT = """Extract and list the key UI elements from this description. For each element include:
1. What type of element it is
2. A brief description of its location/purpose
3. What actions can be taken with it

Format as a simple list:
- Element: [type] - [description] - Actions: [possible actions]"""

CONVERT_PROMPT = """Convert these UI elements into our data model. You MUST map each element type and action to these exact values:

ELEMENT TYPE MAPPING RULES:
- Text input/field → "text_input"
- Menu/Navigation → "menu_bar"
- Image/Logo → "icon"
- Window/Panel → "window"
- Button/Control → "button"
- Search box → "search_bar"

No other element types are allowed. Map each element to its closest match from: {UI_TYPES}

ACTION MAPPING RULES:
Mouse Actions: {MOUSE_ACTIONS}
- Click/Select → "left_click"
- Right Click/Context → "right_click"
- Double Click/Open → "double_click"

Keyboard Actions: {KEYBOARD_ACTIONS}
- Type/Input → "type"
- Enter/Submit → "enter"
- Delete/Remove → "backspace"

DetectedElements Schema:
{SCHEMA}

Return JSON matching this EXACT DetectedElements example:
{EXAMPLE}""" 