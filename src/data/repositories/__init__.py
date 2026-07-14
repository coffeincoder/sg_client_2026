# Repository interfaces package.
# Register concrete JSON implementations as virtual subclasses so that
# isinstance/issubclass checks work without modifying the concrete classes.

from src.data.repositories.interfaces import IZoneRepository, IFileRepository
from src.operations_with_zones.ZoneItemRepository import ZoneItemRepository
from src.operations_with_files.FileItemRepository import FileItemRepository

IZoneRepository.register(ZoneItemRepository)
IFileRepository.register(FileItemRepository)
