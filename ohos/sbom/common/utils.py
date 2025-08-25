import json
import mimetypes
import os
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Tuple, List
from typing import Union
from urllib.parse import urlparse

from packageurl import PackageURL


def read_json(path: Union[str, Path]) -> Any:
    """
    Read and parse a JSON file from the specified path.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data: Any, file_path: str, *, indent: bool = True) -> None:
    """
    Serialize Python object to JSON and write to file.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        if indent:
            json.dump(data, f, indent=4, sort_keys=True, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)


def remove_empty(obj: Any) -> Any:
    """
    Recursively remove empty values from nested dicts/lists.
    Removes: None, "", [], {}, ()
    """
    if isinstance(obj, (dict, OrderedDict)):
        cleaned = OrderedDict()
        for k, v in obj.items():
            cleaned_value = remove_empty(v)
            # Only keep non-empty values
            if cleaned_value not in (None, "", [], {}, ()):
                cleaned[k] = cleaned_value
        return cleaned
    elif isinstance(obj, list):
        cleaned_list = [remove_empty(item) for item in obj]
        # Filter out empty items
        return [item for item in cleaned_list if item not in (None, "", [], {}, ())]
    else:
        return obj


def generate_purl(type: str, namespace: str, name: str,
                  version: str = None, qualifiers: dict = None,
                  subpath: str = None) -> str:
    """
    Generate standard Package URL (purl) string.
    """
    try:
        purl = PackageURL(
            type=type,
            namespace=namespace,
            name=name,
            version=version,
            qualifiers=qualifiers,
            subpath=subpath
        )
        return purl.to_string()
    except Exception as e:
        raise ValueError(f"Invalid PURL fields: {e}") from e


def get_purl_type_from_url(url: str) -> str:
    """
    Infer purl type from URL based on predefined rules.
    """
    if not url or not isinstance(url, str):
        return "generic"

    url_lower = url.lower().strip()

    # Define matching rules: (pattern, purl_type, is_regex)
    rules: List[Tuple[str, str, bool]] = [
        # Hosting platforms (exact domain matches first)
        ("github.com", "github", False),
        ("gitlab.com", "gitlab", False),
        ("gitlab", "gitlab", True),
        ("gitee.com", "gitee", False),
        ("gitcode.net", "gitcode", False),
        ("bitbucket.org", "bitbucket", False),

        # Package types (based on extensions/paths)
        (r"\.src\.rpm$", "rpm", True),
        (r"\.rpm$", "rpm", True),
        (r"\.deb$", "deb", True),
        (r"\.whl$", "pypi", True),
        (r"/pypi/", "pypi", True),
        (r"\.jar$", "maven", True),
        (r"/maven2/", "maven", True),
        (r"\.gem$", "gem", True),
        (r"\.git$", "git", True),

        # Generic source packages
        (r"\.tar\.gz$", "generic", True),
        (r"\.tgz$", "generic", True),
        (r"\.zip$", "generic", True),
        (r"\.tar\.bz2$", "generic", True),
    ]

    for pattern, purl_type, is_regex in rules:
        if is_regex:
            if re.search(pattern, url_lower):
                return purl_type
        else:
            if pattern in url_lower:
                return purl_type

    return "generic"


def is_text_file(path: str) -> bool:
    """
    Determine if file is text-based using mimetype detection.
    """
    if not os.path.isfile(path):
        return False

    # Guess MIME type from extension
    mime_type, _ = mimetypes.guess_type(path)

    # Default to False for unknown types
    if mime_type is None:
        return False

    # Check if MIME type indicates text
    return mime_type.startswith("text/")


def commit_url_of(url: str, commit_id: str) -> str:
    """
    Generate web URL for viewing a specific commit in code hosting platforms.
    """
    # Preserve original input for fallback
    original_url = url.strip() if url else ""
    if not original_url or not commit_id:
        return original_url

    # Clean commit ID (remove non-hex chars)
    cleaned_commit = re.sub(r'[^a-fA-F0-9]', '', commit_id)
    if not cleaned_commit:
        return original_url
    try:
        parsed = urlparse(original_url)
        host = parsed.netloc.lower()
        path = parsed.path.strip("/")

        # Require at least owner/repo in path
        parts = path.split("/")
        if len(parts) < 2:
            return original_url

        owner, repo = parts[0], parts[1]
        base_url = f"https://{host}/{owner}/{repo}"

        # Generate platform-specific commit URLs
        if "gitee.com" in host:
            return f"{base_url}/tree/{commit_id}"
        elif "github.com" in host:
            return f"{base_url}/tree/{commit_id}"
        else:
            return original_url

    except Exception:
        # Fallback to original URL on any parsing error
        return original_url
