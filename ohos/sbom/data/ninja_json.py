from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Callable, Optional

from ohos.sbom.data.build_setting import BuildSetting
from ohos.sbom.data.target import Target


@dataclass
class NinjaJson:
    _build_setting: 'BuildSetting'
    _targets: Dict[str, 'Target']

    @property
    def build_setting(self) -> 'BuildSetting':
        return self._build_setting

    def get_target(self, name: str) -> Optional['Target']:
        return self._targets.get(name)

    def all_targets(self) -> List['Target']:
        return list(self._targets.values())

    def filter_targets(self, predicate: Callable[['Target'], bool]) -> List['Target']:
        return [t for t in self._targets.values() if predicate(t)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "build_settings": asdict(self._build_setting),
            "targets": {
                name: target.to_dict_without_name()
                for name, target in self._targets.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NinjaJson':
        return cls(
            _build_setting=BuildSetting.from_dict(data.get("build_settings", {})),
            _targets={name: Target.from_dict(name, tdict)
                      for name, tdict in data.get("targets", {}).items()},
        )
