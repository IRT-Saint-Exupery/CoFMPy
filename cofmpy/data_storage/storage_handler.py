
from .base_data_storage import BaseDataStorage


class StorageHandler:
    def __init__(self):
        self._storage: list[BaseDataStorage] = []

    def register_storage(self, type: str, config: dict) -> None:
        data_storage = BaseDataStorage.create_data_storage({"type": type, "config": config})
        self._storage.append(data_storage)

    def notify_results(self, type, time: float, data, metadata=None) -> None:
        for storage in self._storage:
            if storage.type_name == type:
                storage.save("", time, data, metadata=None)

