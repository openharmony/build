from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass(frozen=True)
class OpenSource:
    name: str
    license: str
    license_file: str = field(metadata={"source_key": "License File"})
    version_number: str
    owner: str
    upstream_url: str = field(metadata={"source_key": "Upstream URL"})
    description: str
    dependencies: Tuple[str, ...] = field(default_factory=tuple)

    def get_licenses(self) -> List[str]:
        return [lic.strip() for lic in self.license.split(';') if lic.strip()]

    def get_license_files(self) -> List[str]:
        return [f.strip() for f in self.license_file.split(';') if f.strip()]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "license": self.license,
            "license_file": self.license_file,
            "version_number": self.version_number,
            "owner": self.owner,
            "upstream_url": self.upstream_url,
            "description": self.description,
            "dependencies": list(self.dependencies),
            "licenses": list(self.get_licenses()),
            "license_files": list(self.get_license_files())
        }

    @classmethod
    def from_dict(cls, data: dict):
        mapping = {
            'Name': 'name',
            'License': 'license',
            'License File': 'license_file',
            'Version Number': 'version_number',
            'Owner': 'owner',
            'Upstream URL': 'upstream_url',
            'Description': 'description',
            'Dependencies': 'dependencies'
        }
        init_data = {}
        for json_key, attr_name in mapping.items():
            value = data.get(json_key)
            if isinstance(value, str):
                value = value.strip()
            elif value is None:
                value = ""
            if attr_name == "dependencies":
                if isinstance(value, str):
                    value = tuple(v.strip() for v in value.split(';') if v.strip())
                elif isinstance(value, list):
                    value = tuple(value)
                else:
                    value = ()
            init_data[attr_name] = value
        return cls(**init_data)
