from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Any, DefaultDict, Optional, Union

from ohos.sbom.data.ninja_json import NinjaJson
from ohos.sbom.data.target import Target
from templates.metadata.gen_module_info import create_module_info_parser, gen_module_info_data


@dataclass
class InstallModule:
    module_info_file: str


@dataclass
class InstallMatchResult:
    source_target: Target
    matched_targets: List[Target]


class OutputIndex:

    def __init__(self, targets: List[Target]) -> None:
        self._idx: DefaultDict[str, List[Target]] = defaultdict(list)
        for t in targets:
            for out in t.outputs:
                self._idx[out].append(t)

    def lookup(self, output: str) -> List[Target]:
        return self._idx.get(output, [])


class InstallModuleAnalyzer:
    def __init__(self, nj: NinjaJson) -> None:
        self._nj = nj
        self._index = OutputIndex(self._nj.all_targets())
        self._matched_install_module = None
        self._install_enable = None
        self._install_dest = None

    def get_matched_install_module(self) -> Dict[str, InstallMatchResult]:
        if self._matched_install_module is None:
            self._match_all()
        return self._matched_install_module

    def get_enabled_modules(self, install_enable: bool = True):
        if self._matched_install_module is None:
            self._analysis_all_install_enable()
        return [key for key, value in self._install_enable.items() if value == install_enable]

    def get_install_with_dest(self):
        install_src_target = self.get_enabled_modules(install_enable=True)
        return {target_name: self._install_dest[target_name] for target_name in install_src_target}

    def get_install_enable_target(self):
        enabled_modules = set(self.get_enabled_modules(install_enable=True))
        return self._nj.filter_targets(lambda t: t.target_name in enabled_modules)

    def _match_all(self):
        results: Dict[str, InstallMatchResult] = {}
        build_dir = self._nj.build_setting.build_dir

        targets = self._nj.filter_targets(lambda t: not t.testonly)
        for src in targets:
            raw_modules: List[Dict[str, str]] = src.metadata.get("install_modules", [])
            if not raw_modules:
                continue

            modules = [InstallModule(m.get("module_info_file", "")) for m in raw_modules]
            expected_outputs = {
                str(build_dir + m.module_info_file) for m in modules
            }

            matched: List[Target] = []
            for out in expected_outputs:
                matched.extend(self._index.lookup(out))

            dedup = {t.target_name: t for t in matched}
            results[src.target_name] = InstallMatchResult(
                source_target=src,
                matched_targets=list(dedup.values())
            )

            if len(dedup) != len(modules):
                print(f"[Warning] {src.target_name} install_modules not match all outputs")
        self._matched_install_module = results

    def generate_module_info(self, target: Union[Target, str]) -> Optional[Dict[str, Any]]:
        if isinstance(target, str):
            target = next((t for t in self._nj.all_targets() if t.target_name == target), None)
            if not target:
                print(f"[Error] not found analyze target: {target}")
                return None
        create_module_info_parser()
        args = target.args

        args = create_module_info_parser().parse_args(args)
        module_info_data = gen_module_info_data(args)
        return module_info_data

    def _analysis_all_install_enable(self):
        install_results: Dict[str, bool] = {}
        dest_results: Dict[str, list[str]] = {}
        matched_modules = self.get_matched_install_module()

        def process_target(src_target_name: str, target: Target) -> None:
            module_info = self.generate_module_info(target)
            install_enable = False
            dest = []
            if module_info:
                install_enable = module_info.get("install_enable", False)
                dest = module_info.get("dest", [])
            install_results[src_target_name] = install_enable
            dest_results[src_target_name] = dest

        for src_target_name, match_result in matched_modules.items():
            for target in match_result.matched_targets:
                process_target(src_target_name, target)
        self._install_enable = install_results
        self._install_dest = dest_results
