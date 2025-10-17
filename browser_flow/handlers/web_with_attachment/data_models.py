from dataclasses import dataclass
from typing import List


@dataclass
class Attachment:
    title: str
    url: str


@dataclass
class JobPosting:
    title: str
    content: str
    attachments: List[Attachment]
