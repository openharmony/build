import json
import os
import re
from pathlib import Path
from typing import Optional, List, Union, Dict, Any

from ohos.sbom.common.utils import read_json, is_text_file
from ohos.sbom.data.manifest import Manifest
from ohos.sbom.data.ninja_json import NinjaJson
from ohos.sbom.data.opensource import OpenSource


class LocalResourceLoader:
    """
    Local resource loader for OpenHarmony codebase.

    Provides methods to load various resource files from the OpenHarmony source tree
    with caching mechanism to avoid repeated parsing of the same files.
    """

    # Class variables for paths
    _source_root: Optional[str] = None
    _out_root: Optional[str] = None

    # Resource cache: file path/identifier -> parsed object instance
    _resource_cache: Dict[str, object] = {}

    @classmethod
    def set_source_root(cls, source_root: Union[str, Path]) -> None:
        """
        Set the project source root directory path.

        Args:
            source_root: Path to project source root
        """
        src_path = cls._validate_directory(source_root, "Source root path")
        cls._source_root = str(src_path)

    @classmethod
    def set_out_root(cls, out_root: Union[str, Path]) -> None:
        """
        Set the build output directory path.

        Args:
            out_root: Path to build output directory
        """
        out_path = cls._validate_directory(out_root, "Output directory path")
        cls._out_root = str(out_path)

    @classmethod
    def to_local_path(cls, relation_path: Union[str, Path]) -> str:
        """
        Convert a logical path to an absolute filesystem path.

        Args:
            relation_path: Logical path (e.g. "//kernel/entry.c")

        Returns:
            Corresponding absolute local path
        """
        source_root = cls._source_root
        if not relation_path:
            return source_root

        path_str = str(relation_path).strip()

        if os.path.isabs(path_str) and os.path.exists(path_str):
            return os.path.abspath(path_str)

        if path_str.startswith("//"):
            relative_part = path_str[2:]
        else:
            relative_part = path_str.lstrip("/")

        local_path = os.path.join(source_root, relative_part)
        return os.path.normpath(local_path)

    @classmethod
    def load_ninja_json(cls) -> NinjaJson:
        """
        Load and parse the Ninja build configuration file (JSON format) with caching.

        The parsed configuration is cached to avoid repeated file reads and parsing.

        Returns:
            NinjaJson: Parsed build configuration object
        """
        # Check cache first
        cache_key = "ninja_json"
        cached = cls._get_cache_obj(cache_key)
        if cached is not None:
            return cached

        if not cls._source_root:
            raise RuntimeError("Source root directory not set. Call set_source_root() first.")

        # Construct full path to the build configuration file
        gn_gen_path = Path(cls._out_root) / "sbom" / "gn_gen.json"

        # Validate file exists with helpful error message
        if not gn_gen_path.exists():
            raise FileNotFoundError(
                f"Ninja build configuration file not found at: {gn_gen_path.absolute()}\n"
                "To generate this file, add these arguments to build.sh command:\n"
                "  --gn-flags=--ide=json\n"
                "  --gn-flags=--json-file-name=sbom/gn_gen.json\n"
            )

        try:
            # Read and parse the JSON file
            data = json.loads(gn_gen_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in build configuration at {gn_gen_path}: {str(e)}",
                e.doc, e.pos
            )
        except IOError as e:
            raise IOError(
                f"Failed to read build configuration from {gn_gen_path}: {str(e)}"
            )

        try:
            # Create and cache the parsed object
            ninja_json = NinjaJson.from_dict(data)
            cls._add_cache_obj(cache_key, ninja_json)
            return ninja_json
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Failed to convert build configuration data from {gn_gen_path}: {str(e)}"
            )

    @classmethod
    def load_manifest(cls) -> Manifest:
        """
        Load and cache the latest manifest configuration file.

        Returns:
            Manifest: Parsed manifest object
        """
        # Define cache key (consistent with other methods)
        cache_key = "manifest"

        # Check cache first
        cached = cls._get_cache_obj(cache_key)
        if cached is not None:
            return cached

        # Find latest manifest file
        manifest_path = cls._find_latest_manifest()
        if not manifest_path:
            raise FileNotFoundError(
                f"No valid manifest file found in directory: "
                f"{Path(cls._source_root) / '.repo' / 'manifests' / 'tag'}"
            )

        try:
            # Parse manifest file
            manifest = Manifest.from_file(str(manifest_path))

            # Add to cache before returning
            cls._add_cache_obj(cache_key, manifest)

            print(f"Successfully loaded and cached manifest from: {manifest_path}")
            return manifest

        except Exception as e:
            error_msg = (f"Failed to parse manifest file {manifest_path}. "
                         f"Reason: {str(e)}")
            raise ValueError(error_msg) from e

    @classmethod
    def load_opensource(cls, package_path: str) -> Optional[List[OpenSource]]:
        """
        Load OpenSource metadata for a package.

        Args:
            package_path: Logical path to package (e.g. "//third_party/openssl")

        Returns:
            List of OpenSource objects, or None if not found/invalid
        """
        local_path = cls.to_local_path(package_path)
        opensource_file = os.path.join(local_path, "README.OpenSource")

        if not os.path.isfile(opensource_file):
            return None

        data = read_json(opensource_file)
        if not data:
            return None

        if isinstance(data, dict):
            return [OpenSource.from_dict(data)]
        elif isinstance(data, list):
            return [OpenSource.from_dict(item) for item in data if isinstance(item, dict)]
        return None

    @classmethod
    def load_text_file(cls, path: str, max_bytes: int = None) -> str:
        """
        Safely read text file content.

        Args:
            path: Path to file (logical or absolute)
            max_bytes: Maximum bytes to read (optional)

        Returns:
            File content as string, or empty string for non-text files
        """
        abs_path = cls.to_local_path(path)

        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")

        if not is_text_file(abs_path):
            return ""

        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                return f.read(max_bytes) if max_bytes else f.read()
        except UnicodeDecodeError:
            return ""
        except Exception:
            return ""

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached resources."""
        cls._resource_cache.clear()

    @classmethod
    def get_cache_size(cls) -> int:
        """Get current number of cached resources."""
        return len(cls._resource_cache)

    @classmethod
    def _get_cache_obj(cls, obj_name: str) -> Any:
        """Internal method to get cached object by name."""
        return cls._resource_cache.get(obj_name, None)

    @classmethod
    def _add_cache_obj(cls, obj_name: str, obj: Any) -> None:
        """Internal method to add cached object by name."""
        cls._resource_cache[obj_name] = obj

    @classmethod
    def _find_latest_manifest(cls) -> Optional[Path]:
        """
        Find the latest manifest file in .repo/manifests/tag/ directory.

        Looks for files matching pattern: manifest_tag_YYYYMMDD_HHMMSS.xml

        Returns:
            Path to latest manifest file, or None if none found
        """
        if not cls._source_root:
            raise RuntimeError("Source root directory not set. Call set_source_root() first.")

        tag_dir = Path(cls._source_root) / ".repo" / "manifests" / "tag"

        if not tag_dir.exists() or not tag_dir.is_dir():
            print(f"Warning: Manifest tag directory not found: {tag_dir}")
            return None

        pattern = re.compile(r"manifest_tag_(\d{8})_(\d{6})\.xml$")
        manifest_files = []

        for file_path in tag_dir.iterdir():
            if file_path.is_file():
                match = pattern.match(file_path.name)
                if match:
                    timestamp = int(match.group(1) + match.group(2))
                    manifest_files.append((timestamp, file_path))

        if not manifest_files:
            print(f"No manifest files found in {tag_dir}")
            return None

        return max(manifest_files, key=lambda x: x[0])[1]

    @classmethod
    def _validate_directory(cls, path: Union[str, Path], description: str) -> Path:
        """
        Validate that a path exists and is a directory.

        Args:
            path: Path to validate (str or Path)
            description: Description of path for error messages

        Returns:
            Resolved absolute Path object
        """
        resolved_path = Path(path).resolve()

        if not resolved_path.exists():
            raise ValueError(f"{description} does not exist: {resolved_path}")
        if not resolved_path.is_dir():
            raise ValueError(f"{description} is not a directory: {resolved_path}")

        return resolved_path
