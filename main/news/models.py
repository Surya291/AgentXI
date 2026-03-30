from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    title: str
    description: str
    link: str
    pub_date: str
    parsed_at: Optional[datetime] = field(default=None, compare=False)

    @property
    def guid(self) -> str:
        """Unique key for dedup — just use the link."""
        return self.link

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "pub_date": self.pub_date,
            "parsed_at": self.parsed_at.isoformat() if self.parsed_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NewsItem":
        parsed_at = None
        if d.get("parsed_at"):
            try:
                parsed_at = datetime.fromisoformat(d["parsed_at"])
            except ValueError:
                pass
        return cls(
            title=d.get("title", ""),
            description=d.get("description", ""),
            link=d.get("link", ""),
            pub_date=d.get("pub_date", ""),
            parsed_at=parsed_at,
        )
