from dataclasses import dataclass


@dataclass
class FileItem:
    header: str
    filename: str
    text: str
    duration: int
    create_date: str
    current_voice: str = None
    tag: int = 0
    yandex_file: bool = False
    recognized_file: bool = False

    def to_json(self):
        return self.__dict__

    @classmethod
    def from_json(cls, file_item_dict):
        return cls(
            header=file_item_dict.get('header'),
            filename=file_item_dict.get('filename'),
            text=file_item_dict.get('text'),
            duration=round(file_item_dict.get('duration')),
            create_date=file_item_dict.get('create_date'),
            current_voice=file_item_dict.get('current_voice', None),
            tag=file_item_dict.get('tag', 0),
            yandex_file=file_item_dict.get('yandex_file', False),
            recognized_file=file_item_dict.get('recognized_file', False)
        )