# AI Data Processor

This project prepares data for fine-tuning AI models by processing raw data into a common JSONL format.

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. Install the project in editable mode:
   ```
   pip install -e .
   ```

## Usage

To process data, run:

```
process-data
```

## Project Structure

```
project_root/
│
├── src/
│   ├── data_processors/
│   │   ├── __init__.py
│   │   ├── base_processor.py
│   │   └── video_editor_processor.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── file_utils.py
│   └── main.py
│
├── tests/
│   ├── __init__.py
│   ├── test_base_processor.py
│   └── test_video_editor_processor.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── configs/
│   └── config.yaml
│
├── requirements.txt
├── setup.py
├── README.md
└── .gitignore
```

## Files

- `src/data_processors/base_processor.py`: Base data processor class
- `src/data_processors/video_editor_processor.py`: Video editor data processor class
- `src/utils/file_utils.py`: Utility functions for file operations
- `src/main.py`: Main script for processing data
- `tests/__init__.py`: Test module initializer
- `tests/test_base_processor.py`: Unit tests for the base data processor
- `tests/test_video_editor_processor.py`: Unit tests for the video editor data processor
- `data/raw/`: Directory for raw data
- `data/processed/`: Directory for processed data
- `configs/config.yaml`: Configuration file for the project
- `requirements.txt`: List of dependencies
- `setup.py`: Setup script for installing the project
- `README.md`: This README file
- `.gitignore`: Git ignore file