import os
from datetime import datetime

from src.data_processors.video_editor_processor import VideoEditorProcessor

def main():
    # Load configuration (you can use a config file later)
    input_folder = "data/raw/editor"
    output_folder = "data/processed/editor"
    intermediate_folder = "data/intermediate/editor"
    
    date = datetime.now().strftime("%b%d_%H").lower()
    output_file = os.path.join(output_folder, f"editor_{date}.jsonl")

    processor = VideoEditorProcessor(
        input_folder,
        output_folder,
        intermediate_folder,
        test_mode=False,
    )
    
    processor.process_data()
    processor.generate_jsonl(output_file, huggingface_format=False)

if __name__ == "__main__":
    main()