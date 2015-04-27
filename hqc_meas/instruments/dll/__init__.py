# -*- coding: utf-8 -*-

import os
from pyclibrary.utils import (add_header_locations)

add_header_locations([os.path.join(os.path.dirname(__file__), 'headers')])