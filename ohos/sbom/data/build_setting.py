from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class BuildSetting:
    build_dir: str
    default_toolchain: str
    gen_input_files: List[str]
    root_path: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BuildSetting":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in allowed})
