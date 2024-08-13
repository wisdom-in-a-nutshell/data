import os
import tempfile
from src.utils.file_utils import ensure_dir

def test_ensure_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_directory")
        
        # Test creating a new directory
        ensure_dir(test_dir)
        assert os.path.exists(test_dir)
        
        # Test with an existing directory (should not raise an error)
        ensure_dir(test_dir)
        assert os.path.exists(test_dir)