import os
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, List, Union, Set, Optional

from ohos.sbom.analysis.depend_graph import DependGraphAnalyzer
from ohos.sbom.analysis.file_dependency import FileDependencyAnalyzer
from ohos.sbom.analysis.install_module import InstallModuleAnalyzer
from ohos.sbom.analysis.project_dependency import ProjectDependencyAnalyzer
from ohos.sbom.common.utils import generate_purl, get_purl_type_from_url, commit_url_of
from ohos.sbom.data.file_dependence import File
from ohos.sbom.data.manifest import Project
from ohos.sbom.data.opensource import OpenSource
from ohos.sbom.extraction.copyright_and_license_scanner import LicenseFileScanner, FileScanner
from ohos.sbom.extraction.local_resource_loader import LocalResourceLoader
from ohos.sbom.sbom.builder.file_builder import FileBuilder
from ohos.sbom.sbom.builder.package_builder import PackageBuilder
from ohos.sbom.sbom.builder.relationship_builder import RelationshipBuilder
from ohos.sbom.sbom.builder.sbom_meta_data_builder import SBOMMetaDataBuilder
from ohos.sbom.sbom.metadata.sbom_meta_data import RelationshipType, SBOMMetaData, NOASSERTION


class SBOMGenerator:
    def __init__(self, args: ArgumentParser):
        self.args = args
        self.source_ninja_json = None
        self.manifest = None
        self.file_dependence_analyzer = None
        self._install_target_name_dest_map: Dict[str, List[str]] = {}
        self._file_ref_map: Dict[str, str] = {}
        self._file_dep_filter: Dict[str, File] = {}
        self.sbom_builder: SBOMMetaDataBuilder = SBOMMetaDataBuilder()
        self.license_scanner = LicenseFileScanner()
        self.file_scanner = FileScanner()
        self.init()
        self.build_filtered_files()

    def init(self):
        print("Initializing SBOM generator...")
        print("Initializing [1/4]: Loading Manifest and gn-generated JSON ...")
        self.source_ninja_json = LocalResourceLoader.load_ninja_json()
        self.manifest = LocalResourceLoader.load_manifest()
        print("Initializing [2/4]: Determining whether Targets are installed to the image ...")
        install_module_analyzer = InstallModuleAnalyzer(self.source_ninja_json)
        self._install_target_name_dest_map = install_module_analyzer.get_install_with_dest()
        print("Initializing [3/4]: Building Target dependency network ...")
        depend_graph_analyzer = DependGraphAnalyzer(self.source_ninja_json)
        print("Initializing [4/4]: Building dependencies for files installed on the image ...")
        self.file_dependence_analyzer = FileDependencyAnalyzer(depend_graph_analyzer)
        self.file_dependence_analyzer.build_all_install_deps_optimized(self._install_target_name_dest_map.keys())

    def build_filtered_files(self):
        """
        Get _file_dependencies from file_dependence_analyzer,
        filter items whose keys start with "//",
        assign the result to self._file_dep_filter,
        and build self._file_ref_map (path -> file_id).
        """
        raw_files = self.file_dependence_analyzer.get_file_dependencies()

        self._file_dep_filter.clear()
        self._file_ref_map.clear()
        map_source_file: Dict[str, Set[File]] = {}
        for path, file in raw_files.items():
            file_id = path
            self._file_ref_map[path] = file_id
            if path.startswith("//") or "/" not in path[2:]:
                continue
            map_source_file[path] = {item for dep_set in file.get_dependencies().values() for item in dep_set}

        for path, file in raw_files.items():
            if not path.startswith("//") and "/" in path[2:]:
                continue
            for relationship_type in RelationshipType:
                original_deps = file.get_dependencies(relationship_type)
                new_deps = set()
                # Substitute intermediate files with original source references
                for dep in original_deps:
                    new_deps.update(map_source_file.get(dep.relative_path, {dep}))
                file.set_dependencies(relationship_type, new_deps)
            self._file_dep_filter[path] = file

        self._add_install_dest_file()

        print(f"Filtered {len(self._file_dep_filter)} files starting with '//'")
        print(f"Built file_ref_map with {len(self._file_ref_map)} entries")

    def build_file_information(self):
        all_files = self._file_dep_filter

        for file_path, file_obj in all_files.items():
            file_id = self._file_ref_map[file_path]
            file_scanner_ret = self._extract_scanner_info(file_path)
            file = (FileBuilder()
                    .with_file_name(os.path.basename(file_path))
                    .with_file_id(file_id)
                    .with_file_author(file_scanner_ret["fileAuthor"])
                    .with_copyright_text(file_scanner_ret["copyright_text"])
                    )

            self.sbom_builder.add_file(file)

        for file_path, file_obj in all_files.items():
            for relationship_type in RelationshipType:
                dep_file_id_list = []
                dependencies = file_obj.get_dependencies(relationship_type)
                if len(dependencies) == 0:
                    continue
                file_id = self._file_ref_map[file_path]
                for dep in dependencies:
                    dep_id = self._file_ref_map[dep.relative_path]
                    dep_file_id_list.append(dep_id)
                relationship_builder = (RelationshipBuilder().with_relationship_type(relationship_type)
                                        .with_bom_ref(file_id)
                                        .with_depends_on(dep_file_id_list)
                                        )
                self.sbom_builder.add_relationship(relationship_builder)

    def build_package_information(self):
        """Build package information and dependencies for SBOM generation."""
        pdb = ProjectDependencyAnalyzer()
        pdb.build([file for file in self._file_dep_filter.values()])
        all_project_dependence = pdb.get_project_dependence()

        project_bom_refs = self._build_main_packages(all_project_dependence)
        self._build_dependencies(all_project_dependence, project_bom_refs)

    def build_document_information(self):
        doc_builder = self.sbom_builder.start_document()
        doc_builder.with_name(f"{self.args.product}-{self.manifest.default['revision']}").end()

    def build_sbom(self) -> SBOMMetaData:
        print("Building file information...")
        self.build_file_information()
        print("Building package information...")
        self.build_package_information()
        print("Building document information...")
        self.build_document_information()
        print("Generating final SBOM metadata ...")
        sbom_meta_data = self.sbom_builder.build(validate=False)
        print("Generation completed:")
        print("• Packages:", len(sbom_meta_data.packages))
        print("• Files:", len(sbom_meta_data.files))
        print("• Relationships:", len(sbom_meta_data.relationships))
        return sbom_meta_data

    def _get_file_reference(self, dep: File) -> Optional[str]:
        """Get the file reference for a file dependency."""
        return self._file_ref_map.get(dep.relative_path)

    def _get_project_license(self, source_project) -> str:
        """Get the license for a project, defaulting to NOASSERTION if not found."""
        license_scanner_ret = self.license_scanner.scan(source_project.path)
        return license_scanner_ret[0]["license_type"] if len(license_scanner_ret) >= 1 else NOASSERTION

    def _add_relationship(self, source_bom_ref: str, depends_on_refs: List[str], rel_type: RelationshipType) -> None:
        """Add a relationship to the SBOM builder."""
        rb = (RelationshipBuilder()
              .with_bom_ref(source_bom_ref)
              .with_depends_on(depends_on_refs)
              .with_relationship_type(rel_type))
        self.sbom_builder.add_relationship(rb)

    def _add_install_dest_file(self):
        target_name_map_file = self.file_dependence_analyzer.get_target_name_map_file()
        for target_name, dest_list in self._install_target_name_dest_map.items():  # 使用更清晰的命名
            file_list = target_name_map_file.get(target_name, [])
            stripped_file_list = [f for f in file_list if f.is_stripped]
            if not file_list:
                continue
            for dest in dest_list:
                dest_file = File(dest, None)

                if len(stripped_file_list) == 1:
                    dest_file.add_dependency(RelationshipType.COPY_OF, stripped_file_list[0])
                else:
                    dest_filename = os.path.basename(dest)
                    matched_files = [
                        f for f in stripped_file_list
                        if os.path.basename(f.relative_path) == dest_filename
                    ]
                    if matched_files:
                        for src_file in matched_files:
                            dest_file.add_dependency(RelationshipType.COPY_OF, src_file)
                    else:
                        print("Warning: Files on the image failed to match with Targets: {}".format(dest))
                        pass
                self._file_dep_filter[dest] = dest_file
                file_id = dest
                self._file_ref_map[dest] = file_id

    def _extract_scanner_info(self, file_path: Union[str, Path]) -> Dict:
        """
        Extract license and copyright information from the scan result of a file.

        Args:
            file_path (str or Path): Path to the file being scanned.

        Returns:
            Dict: A dictionary containing:
                - concluded_license: The primary license (first in list) or NOASSERTION
                - license_info_in_files: List of detected licenses or [NOASSERTION]
                - copyright_text: Copyright statement if found
                - fileAuthor: Comma-separated list of filtered authors/holders
        """
        # Scan the file and extract results
        ret = self.file_scanner.scan(file_path)
        licenses = ret.get("licenses", [])
        copyrights = ret.get("copyrights", [])

        authors = set()
        copyright_text = NOASSERTION

        # Define filtering rules for invalid holder patterns
        invalid_prefixes = ('by ', 'copyright', 'all rights', 'distributed', 'licensed')
        min_len, max_len = 2, 50

        # Process each copyright entry
        for cp in copyrights:
            if not isinstance(cp, dict):
                continue

            # Extract copyright statement (use first non-empty one)
            if copyright_text == NOASSERTION:
                statement = cp.get("statement")
                if statement:
                    copyright_text = statement

            # Extract and normalize holder
            holder = cp.get("holder", "").strip()
            if not holder:
                continue

            # Split comma-separated holders and clean them
            holders = [h.strip() for h in holder.split(",") if h.strip()]
            filtered_holders = self._filter_holders(holders, invalid_prefixes, min_len, max_len)
            authors.update(filtered_holders)

        # Format final author string
        file_author = ", ".join(sorted(authors)) if authors else NOASSERTION

        return {
            "concluded_license": licenses[0] if licenses else NOASSERTION,
            "license_info_in_files": licenses or [NOASSERTION],
            "copyright_text": copyright_text,
            "fileAuthor": file_author
        }

    def _filter_holders(self, holders: List[str], invalid_prefixes: tuple, min_len: int, max_len: int) -> List[str]:
        """Filter out invalid holders based on prefix, length, and format."""
        filtered = []
        for h in holders:
            h_lower = h.lower()
            if (h_lower.startswith(invalid_prefixes) or
                    len(h) < min_len or
                    len(h) > max_len or
                    ('.' in h and h.count('.') > 2)):
                continue
            filtered.append(h)
        return filtered

    def _build_dependencies(self, all_project_dependence: Dict, project_bom_refs: Dict) -> None:
        """Build dependency relationships for all projects."""
        for name, project_dependence in all_project_dependence.items():
            source_bom_ref = project_bom_refs.get(project_dependence.source_project.name)
            if not source_bom_ref:
                continue

            for rel_type in RelationshipType:
                dependencies = project_dependence.get_dependencies(rel_type)
                if not dependencies:
                    continue

                depends_on_refs = self._process_dependencies(dependencies, project_bom_refs)
                if depends_on_refs:
                    self._add_relationship(source_bom_ref, depends_on_refs, rel_type)

    def _process_dependencies(self, dependencies: List, project_bom_refs: Dict) -> List[str]:
        """Process dependencies and return list of bom_refs."""
        depends_on_refs = []

        for dep in dependencies:
            if isinstance(dep, Project):
                if dep.name in project_bom_refs:
                    depends_on_refs.append(project_bom_refs[dep.name])
            elif isinstance(dep, OpenSource):
                depends_on_refs.append(self._process_opensource_dependency(dep, project_bom_refs))
            elif hasattr(dep, "name") and dep.name in project_bom_refs:
                depends_on_refs.append(project_bom_refs[dep.name])
            elif isinstance(dep, File):
                file_ref = self._get_file_reference(dep)
                if file_ref:
                    depends_on_refs.append(file_ref)

        return depends_on_refs

    def _build_main_packages(self, all_project_dependence: Dict) -> Dict:
        """Build main package information and return bom_refs mapping."""
        project_bom_refs = {}
        package_version = self.manifest.default["revision"]

        for name, project_dependence in all_project_dependence.items():
            source_project = project_dependence.source_project
            purl = self.manifest.purl_of(source_project)
            project_bom_refs[source_project.name] = purl

            pb = self._create_main_package_builder(
                name=name,
                source_project=source_project,
                purl=purl,
                package_version=package_version
            )
            self.sbom_builder.add_package(pb)

        return project_bom_refs

    def _process_opensource_dependency(self, dep: OpenSource, project_bom_refs: Dict) -> str:
        """Process an open source dependency and return its bom_ref."""
        purl = generate_purl(
            pkg_type=get_purl_type_from_url(dep.upstream_url),
            namespace="upstream",
            name=dep.name,
            version=dep.version_number,
        )

        if purl not in project_bom_refs:
            pb = (PackageBuilder()
                  .with_name(dep.name)
                  .with_purl(purl)
                  .with_bom_ref(purl)
                  .with_license_concluded(dep.license)
                  .with_version(dep.version_number)
                  .with_download_location(dep.upstream_url)
                  .with_type("library"))
            self.sbom_builder.add_package(pb)

        return purl

    def _create_main_package_builder(self, name: str, source_project, purl: str, package_version: str):
        """Create a PackageBuilder for main project packages."""
        url = self.manifest.remote_url_of(source_project)
        parsed_license = self._get_project_license(source_project)

        return (PackageBuilder()
                .with_name(name)
                .with_purl(purl)
                .with_bom_ref(purl)
                .with_type(source_project.type)
                .with_supplier("Organization: OpenHarmony")
                .with_group("OpenHarmony")
                .with_license_declared(parsed_license)
                .with_version(package_version)
                .with_download_location(commit_url_of(url, source_project.revision))
                .with_type(source_project.type)
                .with_comp_platform(self.args.platform))
