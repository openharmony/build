from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from typing import Set

from ohos.sbom.data.target import Target
from ohos.sbom.sbom.metadata.sbom_meta_data import RelationshipType


class FileType(Enum):
    C_HEADER = 'h'
    C_SOURCE = 'c'
    CPP_SOURCE = 'cpp'
    CXX_SOURCE = 'cc'
    RUST_SOURCE = 'rs'

    SHARED_LIBRARY = 'so'
    STATIC_LIBRARY = 'a'
    WINDOWS_DLL = 'dll'
    WINDOWS_LIB = 'lib'
    RUST_STATIC_LIBRARY = 'rlib'

    TEXT = 'txt'
    JSON = 'json'

    HAP = 'hap'
    IPA = 'ipa'
    ZIP = 'zip'
    TAR = 'tar'
    GZ = 'gz'
    BZ2 = 'bz2'

    OBJECT_FILE = 'o'
    DEPENDENCY_FILE = 'd'

    ABC = 'abc'

    UNKNOWN = 'unknown'

    @property
    def is_shared_library(self) -> bool:
        return self in {FileType.SHARED_LIBRARY, FileType.WINDOWS_DLL}

    @property
    def is_static_library(self) -> bool:
        return self in {FileType.STATIC_LIBRARY, FileType.WINDOWS_LIB, FileType.RUST_STATIC_LIBRARY}

    @property
    def is_source_code(self) -> bool:
        return self in {
            FileType.C_SOURCE,
            FileType.CPP_SOURCE,
            FileType.CXX_SOURCE,
            FileType.RUST_SOURCE,
            FileType.C_HEADER
        }

    @property
    def is_intermediate(self) -> bool:
        return self in {FileType.OBJECT_FILE, FileType.DEPENDENCY_FILE}

    @property
    def is_data_file(self) -> bool:
        return self in {FileType.TEXT, FileType.JSON}

    @property
    def is_package(self) -> bool:
        return self in {
            FileType.HAP, FileType.IPA, FileType.ZIP,
            FileType.TAR, FileType.GZ, FileType.BZ2
        }

    @property
    def is_bytecode(self) -> bool:
        return self == FileType.ABC

    @property
    def is_library(self) -> bool:
        return self.is_static_library or self.is_shared_library

    @property
    def is_object_file(self) -> bool:
        return self == FileType.OBJECT_FILE


class File:
    """Represents a file with dependencies and build relationships"""

    __slots__ = ('_relative_path', '_source_target', '_dependencies', '_file_type')

    def __init__(
            self,
            relative_path: str,
            source_target: Optional['Target'],
            file_type: Optional['FileType'] = None
    ):
        self._relative_path = relative_path
        self._source_target = source_target

        self._file_type = file_type if file_type is not None else self._determine_file_type()

        self._dependencies = {
            type: set()
            for type in RelationshipType
        }

    @property
    def relative_path(self) -> str:
        return self._relative_path

    @property
    def source_target(self) -> 'Target':
        return self._source_target

    @property
    def is_final_artifact(self) -> bool:
        return (self.is_shared_library or
                self.is_bytecode or
                self.is_package)

    @property
    def is_stripped(self):
        return "unstripped/" not in self.relative_path

    @property
    def is_source_code(self) -> bool:
        return self._file_type.is_source_code if self._file_type else False

    @property
    def is_object_file(self) -> bool:
        return self._file_type == FileType.OBJECT_FILE if self._file_type else False

    @property
    def is_intermediate(self) -> bool:
        return self._file_type.is_intermediate if self._file_type else False

    @property
    def is_bytecode(self) -> bool:
        return self._file_type == FileType.ABC if self._file_type else False

    @property
    def is_library(self) -> bool:
        return self._file_type.is_library if self._file_type else False

    @property
    def is_static_library(self) -> bool:
        return self._file_type.is_static_library if self._file_type else False

    @property
    def is_shared_library(self) -> bool:
        return self._file_type.is_shared_library if self._file_type else False

    @property
    def is_data_file(self) -> bool:
        return self._file_type.is_data_file if self._file_type else False

    @property
    def is_package(self) -> bool:
        return self._file_type.is_package if self._file_type else False

    def add_dependency(self, dep_type: RelationshipType, target: 'File') -> None:
        if dep_type not in self._dependencies:
            raise ValueError(f"Invalid dependency type: {dep_type}")

        self._dependencies[dep_type].add(target)

    def add_dependency_list(self, dep_type: RelationshipType, file_list: List['File']) -> None:
        for file in file_list:
            self.add_dependency(dep_type, file)

    def get_dependencies(self, dep_type: Optional[RelationshipType] = None):
        if dep_type:
            return self._dependencies.get(dep_type, set())
        return self._dependencies

    def set_dependencies(self, dep_type: RelationshipType, file_list: Set['File']):
        self._dependencies[dep_type] = set(file_list)

    def add_dependency_by_file_type(self, file: 'File') -> None:
        dependency_type = self._determine_dependency_type(file)
        self.add_dependency(dependency_type, file)

    def add_dependency_list_by_file_type(self, file_list: List['File']) -> None:
        for file in file_list:
            self.add_dependency_by_file_type(file)

    def get_file_type_name(self) -> Optional[str]:
        if self._file_type:
            name = self._file_type.name.lower()
            return name
        return None

    def to_dict(self) -> Dict[str, Any]:
        source_target_name = None
        source_target_type = None
        if self._source_target is not None:
            source_target_name = getattr(self._source_target, 'target_name', None)
            source_target_type = getattr(self._source_target, 'type', None)

        dependencies = {}
        for dep_type, file_set in self._dependencies.items():
            path_list = [f.relative_path for f in file_set if hasattr(f, 'relative_path')]
            dependencies[dep_type.value] = path_list

        file_type_name = self.get_file_type_name()

        return {
            "source_target_type": source_target_type,
            "file_type": file_type_name,
            "relative_path": self.relative_path,
            "source_target": source_target_name,
            "dependencies": dependencies
        }

    def _determine_file_type(self) -> Optional[FileType]:
        if not self._relative_path:
            return None

        ext = Path(self._relative_path).suffix.lower().lstrip('.')

        if ext.startswith('so'):
            return FileType.SHARED_LIBRARY

        if ext in ['gz', 'bz2']:
            stem_ext = Path(self._relative_path).stem.split('.')[-1].lower()
            if stem_ext in ['tar', 'zip']:
                return FileType(stem_ext)

        if 'obj/' in self._relative_path and self._relative_path.endswith('.o'):
            return FileType.OBJECT_FILE

        for item in FileType:
            if item.value == ext:
                return item

        if self._relative_path.endswith('.a'):
            return FileType.STATIC_LIBRARY
        if self._relative_path.endswith('.so'):
            return FileType.SHARED_LIBRARY
        if self._relative_path.endswith('.dll'):
            return FileType.WINDOWS_DLL
        if self._relative_path.endswith('.lib'):
            return FileType.WINDOWS_LIB

        return FileType.UNKNOWN

    def _determine_dependency_type(self, file: 'File') -> RelationshipType:
        """Determine the dependency type using a lookup table."""
        dependency_rules = [
            # (self condition, file condition, dependency type)
            (self.is_shared_library, file.is_static_library, RelationshipType.STATIC_LINK),
            (self.is_shared_library, file.is_shared_library, RelationshipType.DYNAMIC_LINK),
            (self.is_shared_library, lambda f: f.is_source_code or f.is_intermediate, RelationshipType.GENERATED_FROM),
            (self.is_static_library, file.is_shared_library, RelationshipType.DEPENDS_ON),
            (self.is_static_library, lambda f: f.is_source_code or f.is_intermediate, RelationshipType.GENERATED_FROM),
            (self.is_static_library, file.is_static_library, RelationshipType.DEPENDS_ON),
            (self.is_data_file, lambda f: f.is_source_code or f.is_intermediate, RelationshipType.GENERATED_FROM),
            (self.is_package, lambda _: True, RelationshipType.GENERATED_FROM),
            (self.is_intermediate, file.is_source_code, RelationshipType.GENERATED_FROM),
            (self.is_intermediate, lambda f: f.is_intermediate and f.relative_path.endswith('.o'),
             RelationshipType.OTHER),
            (self.is_bytecode, lambda f: f.is_source_code or f.is_intermediate, RelationshipType.GENERATED_FROM),
            (lambda s: s.source_target.type == 'executable', file.is_static_library, RelationshipType.STATIC_LINK),
            (lambda s: s.source_target.type == 'executable', file.is_shared_library, RelationshipType.DYNAMIC_LINK),
            (lambda s: s.source_target.type == 'executable', lambda f: f.is_source_code or f.is_intermediate,
             RelationshipType.GENERATED_FROM),
        ]
        for self_cond, file_cond, dep_type in dependency_rules:
            if self_cond(self) and file_cond(file):
                return dep_type
        return RelationshipType.DEPENDS_ON
