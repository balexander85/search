from search.util import format_file_size, format_file_size_to_int


class Result:
    """Create Search Result object with a parsed dictionary."""

    def __init__(self, obj: dict):
        self.name: str = obj.get("name")
        self.media_type: str = obj.get("media_type", "")
        self.category: str = obj.get("category", "")
        self.seeders: int = int(obj["seeders"])
        self.leachers: int = int(obj["leachers"])
        self.file_size: str = format_file_size(obj.get("file_size", ""))
        self.file_size_int: int = format_file_size_to_int(self.file_size)
        self.vip_status: bool = True if obj.get("vip_status") else False
        self.trusted: bool = True if obj.get("trusted") else False
        self.href: str = obj.get("href")
        self.comment_count: int = int(obj.get("comment_count"))
        self.comments_section: [str] = obj.get("comments_section", [])
        self.uploader: str = obj.get("uploader")
        self.magnet_link: str = obj.get("magnet_link")

    def __str__(self) -> str:
        """Return str(self)."""
        return (
            f"{self.name} | Size: {self.file_size} | Seed: {self.seeders} "
            f"| Leach: {self.leachers} | Trusted: {self.trusted} |"
            f" VIP: {self.vip_status} | Uploader: {self.uploader}\n"
            f"    ML: {self.magnet_link}   \nComments: {self.comments_section}"
        )

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"{self.name}"

    def __hash__(self):
        """Return hash(self)."""
        return hash((self.name, self.uploader, self.magnet_link))

    def __eq__(self, other: "Result"):
        """Return self==value."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return (
            self.name == other.name
            and self.uploader == other.uploader
            and self.magnet_link == other.magnet_link
        )
