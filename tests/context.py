''' Add context for use in tests '''
import os
import sys
import nikoniko  # pylint: disable=unused-import

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
