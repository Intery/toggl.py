import os
import sys
import logging

sys.path.insert(0, os.path.abspath('..'))

import toggl_track


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
