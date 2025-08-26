#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (c) 2025 Northeastern University
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import xml.etree.ElementTree as ET
from typing import Optional, Union

from ohos.sbom.common.utils import generate_purl, get_purl_type_from_url
from ohos.sbom.data.target import Target


class Remote:
    def __init__(self, name, fetch, review=""):
        self._name = name
        self._fetch = fetch
        self._review = review

    @property
    def name(self):
        return self._name

    @property
    def fetch(self):
        return self._fetch

    @property
    def review(self):
        return self._review

    @staticmethod
    def from_element(element):
        name = element.attrib.get("name", "")
        fetch = element.attrib.get("fetch", "")
        review = element.attrib.get("review", "")
        return Remote(name, fetch, review)


class Project:
    def __init__(self, name, path, revision, upstream, dest_branch, groups, remote):
        self._name = name
        self._path = path
        self._revision = revision
        self._upstream = upstream
        self._dest_branch = dest_branch
        self._groups = groups
        self._remote = remote
        self._linkfiles = []

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def revision(self):
        return self._revision

    @property
    def upstream(self):
        return self._upstream

    @property
    def dest_branch(self):
        return self._dest_branch

    @property
    def groups(self):
        return self._groups

    @property
    def remote(self):
        return self._remote

    @property
    def linkfiles(self):
        return self._linkfiles

    @property
    def type(self):
        if "application" in self._path:
            return "application"
        elif "framework" in self._path:
            return "framework"
        return "library"

    @staticmethod
    def from_element(element):
        name = element.attrib.get("name", "")
        path = element.attrib.get("path", "")
        revision = element.attrib.get("revision", "")
        upstream = element.attrib.get("upstream", "")
        dest_branch = element.attrib.get("dest-branch", "")
        groups = element.attrib.get("groups", "").split(",")
        remote = element.attrib.get("remote", "")
        project = Project(name, path, revision, upstream, dest_branch, groups, remote)

        for linkfile_element in element.findall("linkfile"):
            src = linkfile_element.attrib.get("src", "")
            dest = linkfile_element.attrib.get("dest", "")
            if src and dest:
                project.add_linkfile(src, dest)

        return project

    def add_linkfile(self, src, dest):
        self._linkfiles.append({"src": src, "dest": dest})


class Manifest:

    def __init__(self):
        self._remotes = []
        self._default = None
        self._projects = []

    @property
    def remotes(self):
        return self._remotes

    @property
    def default(self):
        return self._default

    @property
    def projects(self):
        return self._projects

    @staticmethod
    def from_file(file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()

        manifest = Manifest()

        # Parse remote elements
        for remote_element in root.findall("remote"):
            remote = Remote.from_element(remote_element)
            manifest.add_remote(remote)

        # Parse default element
        default_element = root.find("default")
        if default_element is not None:
            remote = default_element.attrib["remote"]
            revision = default_element.attrib["revision"]
            sync_j = default_element.attrib["sync-j"]
            manifest.set_default(remote, revision, sync_j)

        # Parse project elements
        for project_element in root.findall("project"):
            project = Project.from_element(project_element)
            manifest.add_project(project)

        return manifest

    def find_project(self, src: Optional[Union[str, Target]]) -> Optional[Project]:
        if isinstance(src, str):
            target_name = src
        else:
            target_name = src.target_name
        if not target_name.startswith("//"):
            return None
        path_part = target_name[2:].split(":")[0]
        matched_projects = []
        for project in self._projects:
            project_path = project.path
            if path_part.startswith(project_path):
                matched_projects.append((project, len(project_path)))

        if matched_projects:
            matched_projects.sort(key=lambda x: -x[1])
            return matched_projects[0][0]
        else:
            return None

    def add_remote(self, remote):
        self._remotes.append(remote)

    def set_default(self, remote, revision, sync_j):
        self._default = {"remote": remote, "revision": revision, "sync-j": sync_j}

    def add_project(self, project):
        self._projects.append(project)

    def remote_url_of(self, project, target_remote: Remote = None):
        if not project or not hasattr(project, 'name'):
            return ""
        if target_remote is None:
            target_remote = self.remote_of(project)
        if not target_remote:
            return ""
        fetch = target_remote.fetch.strip()
        project_name = project.name.strip()

        if (not fetch or fetch == '.') and hasattr(target_remote, 'review'):
            fetch = target_remote.review.strip()

        if fetch:
            fetch = fetch.rstrip('/') + '/' if fetch else ''
            url = f"{fetch}{project_name}"
        else:
            url = project_name

        url = url.replace('//', '/').replace(':/', '://')

        return url

    def remote_of(self, project) -> Optional[Remote]:
        if project.remote != "":
            remote_name = project.remote
        elif self._default is not None:
            remote_name = self._default["remote"]
        else:
            return None
        target_remote = next(
            (remote for remote in self._remotes if remote.name == remote_name),
            None
        )
        return target_remote

    def purl_of(self, project, target_remote: Remote = None) -> Optional[str]:
        if target_remote is None:
            target_remote = self.remote_of(project)
        if not target_remote or not target_remote.fetch:
            raise ValueError(f"No fetch URL found for project: {project.name}")

        url = self.remote_url_of(project, target_remote)
        return generate_purl(
            pkg_type=get_purl_type_from_url(url),
            namespace="OpenHarmony",
            name=project.name,
            version=project.revision,
        )
