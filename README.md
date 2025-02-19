# Computer Use Task List Agent

A modular computer automation agent powered by GPT-4 Vision and Grounding DINO.

## Overview

This project demonstrates a robust approach to building an AI-powered computer automation agent, focusing first on the critical task planning component. The system uses a large vision-language model (GPT-4) to interpret user intentions and generate structured task plans.

### Key Features

- **Modular Architecture**: Each component (task planner, vision system, automation tools) is developed and tested independently
- **Strong Data Model**: Ensures type safety and validation across all system components
- **Test-Driven Development**: Comprehensive testing with mocks validates core functionality
- **Extensible Design**: Ready for integration with Grounding DINO for vision and PyAutoGUI for automation

### Why GPT-4?

While smaller LLMs are often sufficient for many tasks, complex computer automation requires:
- Understanding nuanced user intentions
- Breaking down tasks into logical sequences
- Handling dynamic feedback and error states
- Managing complex context across multiple steps

This complexity necessitates a more capable model like GPT-4, especially when combined with vision capabilities for UI interaction.

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key (for GPT-4)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd computer_use_agent

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies as editable package
pip install --upgrade pip
pip install -e .

# Set up environment variables
touch .env
# Add your OpenAI API key to .env: 'OPENAI_API_KEY=...'
```

### Running Tests

```bash
# Run all tests
python -m pytest tests

# Run specific test files
python -m pytest tests/test_mock_llm.py
python -m pytest tests/test_task_planner.py
python -m pytest tests/test_mock_screenshot_agent.py
```

## Project Structure

```
computer_use_agent/
├── src/
│   ├── data_model.py      # Core data structures
│   └── task_planner.py    # Task planning logic
├── tests/
│   ├── mocks/             # Mock implementations
│   └── test_mock_llm.py   # Test cases
└── README.md
```

## Development Approach

1. **Task Planning**: First component to be implemented, using GPT-4 to generate structured task plans
2. **Vision System**: Will integrate Grounding DINO for UI element detection (future)
3. **Automation**: Will add PyAutoGUI for computer control (future)

This step-by-step approach allows us to validate each component independently, ensuring robust functionality before integration.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

[Your chosen license]
