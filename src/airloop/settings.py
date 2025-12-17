from typing import Dict, List, Optional
from dataclasses import dataclass, field

import yaml

@dataclass
class UserConfig:
    base_url: str
    api_key: str
    model_name: str
    output_streaming: bool = False
    

