import os
from resolver.interface.args_resolver_interface import ArgsResolverInterface
from util.io_util import IoUtil
from resources.global_var import CURRENT_BUILD_DIR, CURRENT_OHOS_ROOT

class ArgsResolver(ArgsResolverInterface):
    @staticmethod
    def parse_command_args(input_args) -> dict:
        parsed = {}
        i = 0
        while i < len(input_args):
            if input_args[i].startswith('--'):
                key = input_args[i]
                if i + 1 < len(input_args) and not input_args[i+1].startswith('--'):
                    value = input_args[i+1]
                    if key in parsed:
                        if not isinstance(parsed[key], list):
                            parsed[key] = [parsed[key]]
                        parsed[key].append(value)
                    else:
                        parsed[key] = value
                    i += 2
                else:
                    parsed[key] = True
                    i += 1
            else:
                parsed.setdefault('positional_input_args', []).append(input_args[i])
                i += 1
        return parsed

    @staticmethod
    def read_indep_whitelist() -> dict:
        whitelist_path = os.path.join(CURRENT_BUILD_DIR, 'indep_component_whitelist.json')
        return IoUtil.read_json_file(whitelist_path)

    @staticmethod
    def is_indep_args(input_args) -> tuple[bool, list]:
        whitelist = ArgsResolver.read_indep_whitelist()
        parsed_args = ArgsResolver.parse_command_args(input_args)
        
        if not ArgsResolver._is_product_in_whitelist(parsed_args, whitelist):
            return False, []
        
        components = ArgsResolver._parse_and_validate_components(parsed_args, whitelist)
        if not components:
            return False, []
        
        if ArgsResolver._has_unsupported_args(parsed_args, whitelist):
            return False, components
        
        return True, components

    @staticmethod
    def _is_product_in_whitelist(parsed_args: dict, whitelist: dict) -> bool:
        product_name = parsed_args.get('--product-name')
        return product_name is not None and product_name in whitelist.get('product-name', [])

    @staticmethod
    def _parse_and_validate_components(parsed_args: dict, whitelist: dict) -> list:
        build_target = parsed_args.get('--build-target')
        components = ArgsResolver.parse_component_name(build_target)
        
        if not components:
            return []
        
        whitelist_components = whitelist.get('components', [])
        if all(comp in whitelist_components for comp in components):
            return components
        return []

    @staticmethod
    def _has_unsupported_args(parsed_args: dict, whitelist: dict) -> bool:
        unsupported_args = whitelist.get('unsupport-args', [])
        for arg in parsed_args:
            if arg != 'positional_input_args' and arg in unsupported_args:
                return True
        return False

    @staticmethod
    def parse_component_name(build_targets) -> list or bool:
        targets = ArgsResolver._normalize_build_targets(build_targets)
        if not targets:
            return False
        
        component_names = []
        for target in targets:
            component_name = ArgsResolver._get_component_name_from_target(target)
            if not component_name:
                return False
            component_names.append(component_name)
        
        return component_names if component_names else False

    @staticmethod
    def _normalize_build_targets(build_targets) -> list or None:
        if isinstance(build_targets, str):
            return [build_targets]
        if isinstance(build_targets, list):
            return build_targets
        return None

    @staticmethod
    def _get_component_name_from_target(build_target: str) -> str or None:
        bundle_rel_path = ArgsResolver.find_deepest_bundle_json(build_target)
        if not bundle_rel_path:
            return None
        
        bundle_path = os.path.join(CURRENT_OHOS_ROOT, bundle_rel_path)
        bundle_json = IoUtil.read_json_file(bundle_path)
        return bundle_json.get("component", {}).get("name")

    @staticmethod
    def find_deepest_bundle_json(build_str: str) -> str or None:
        base_path = build_str.split(':')[0]
        deepest_bundle = None
        current_path = ""
        
        for part in base_path.split(os.sep):
            current_path = os.path.join(current_path, part)
            if os.path.isdir(current_path):
                bundle_path = os.path.join(current_path, 'bundle.json')
                if os.path.isfile(bundle_path):
                    deepest_bundle = bundle_path
        
        return deepest_bundle

    @staticmethod
    def get_indep_args(sys_argv, component_name_list) -> list:
        new_args = []
        added_components = False
        added_i = False
        
        for arg in sys_argv:
            if arg == '--product-name':
                sys_argv.remove(sys_argv[sys_argv.index(arg) + 1])
                continue
            
            if arg == '--build-target':
                if not added_components:
                    new_args.extend(component_name_list)
                    added_components = True
                if not added_i:
                    new_args.append('-i')
                    added_i = True
                sys_argv.remove(sys_argv[sys_argv.index(arg) + 1])
                continue
            
            new_args.append(arg)
        
        return new_args