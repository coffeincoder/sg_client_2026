"""
Repository interfaces for the KSB client data layer.

These ABCs define the contract that any zone/file storage backend must satisfy.
Currently the only backend is JSON (ZoneItemRepository / FileItemRepository).
SQL or other backends can be added later by implementing these interfaces.

Concrete classes are registered as virtual subclasses in __init__.py via
IZoneRepository.register() / IFileRepository.register() — the concrete classes
are NOT modified.
"""

from abc import ABC, abstractmethod


class IZoneRepository(ABC):
    """
    Interface for zone storage.

    Instance attribute guaranteed by all implementations:
        all_zones (list[Orange]) — the in-memory list of zone objects.
            It is a plain instance attribute, not a property; do NOT declare it
            as @abstractmethod to avoid breaking the JSON implementation.

    Methods used by ZonesViewModel / MainWindow (YAGNI — only these are listed):
    """

    @abstractmethod
    def add_zone(self, zone):
        """Add a new zone to the repository."""
        ...

    @abstractmethod
    def add_zone_from_file(self, file):
        """Load a zone definition from a file path and add it to the repository."""
        ...

    @abstractmethod
    def remove_zone(self, zone):
        """Remove a zone from the repository."""
        ...

    @abstractmethod
    def get_all(self):
        """Return all zones as a list."""
        ...

    @abstractmethod
    def save(self, zones=None):
        """
        Persist the current state of zones.

        Some call-sites pass the zone list explicitly (zones_repo.save(ZONE_LIST));
        others may call save() with no arguments.  Implementations must accept
        both forms.
        """
        ...


class IFileRepository(ABC):
    """
    Interface for audio-file item storage.

    Instance attribute guaranteed by all implementations:
        file_list (list[FileItem]) — the in-memory list of file items.
            Plain instance attribute; not declared @abstractmethod for the same
            reason as IZoneRepository.all_zones.

    Methods used by FilesViewModel / MainWindow (YAGNI — only these are listed):
    """

    @abstractmethod
    def add_file(self, file_item):
        """Add a FileItem to the repository."""
        ...

    @abstractmethod
    def get(self):
        """Return all file items (list[FileItem])."""
        ...

    @abstractmethod
    def sort_list(self, sort_key="create_date", reverse_key=True):
        """Return a sorted copy of the file list."""
        ...

    @abstractmethod
    def save(self):
        """Persist the current file list to disk."""
        ...

    @abstractmethod
    def remove_file(self, file_item):
        """Remove a FileItem from the repository."""
        ...
