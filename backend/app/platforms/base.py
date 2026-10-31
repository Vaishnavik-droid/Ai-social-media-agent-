from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.publishing import PlatformResult


class BasePlatformAdapter(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the platform, e.g. 'bluesky', 'linkedin', 'facebook', 'pinterest', 'youtube'."""
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Verify whether credentials and connection to the platform are valid."""
        pass

    @abstractmethod
    async def publish_post(
        self,
        content: str,
        media_url: Optional[str] = None,
        dry_run: bool = False,
        **kwargs
    ) -> PlatformResult:
        """Publish text content and optional media to the platform, with optional dry_run mock mode."""
        pass
