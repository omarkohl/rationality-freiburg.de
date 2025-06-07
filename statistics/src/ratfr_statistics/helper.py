import os
import yaml
from typing import List, Dict

EVENTS_WEBDIR = "../website/content/events/"


def get_page_metadata(page: str) -> Dict:
    """
    This function reads the metadata from a Hugo page.
    """
    yaml_content = ""
    in_yaml = False
    with open(page) as f:
        lines = f.readlines()
        for line in lines:
            if in_yaml and line == "---\n":
                break
            if in_yaml:
                yaml_content += line
            if not in_yaml and line == "---\n":
                in_yaml = True
    data = yaml.safe_load(yaml_content)
    return data


def get_event_metadata(dates: List[str]):
    metadata = dict()
    for d in dates:
        dirs = [
            f for f in os.listdir(EVENTS_WEBDIR) if f.startswith(d.strftime("%Y-%m-%d"))
        ]
        if len(dirs) == 0:
            raise ValueError(f"No directory for {d} exists")
        elif len(dirs) > 1:
            raise ValueError(f"More than one directory for {d} exists")

        event_dir = os.path.join(EVENTS_WEBDIR, dirs[0])
        event_data = get_page_metadata(os.path.join(event_dir, "_index.md"))
        metadata[d] = event_data

    return metadata
