from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Optional, List, Union, BinaryIO

from telegram import (
    InputMediaPhoto,
    InputMediaVideo,
    InlineKeyboardButton,
    KeyboardButton,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
)


@dataclass_json
@dataclass
class Image:
    media: List[InputMediaPhoto] = field(default_factory=list)

    @staticmethod
    def set(file: Union[List, str, bytes]):
        result = []
        if isinstance(file, list):
            if len(file) == 1:
                result = file
            else:
                for item in file:
                    result.append(InputMediaPhoto(media=item))
        else:
            result = [file]
        return Image(media=result)


@dataclass_json
@dataclass
class Video:
    media: List[InputMediaVideo] = field(default_factory=list)

    @staticmethod
    def set(file: Union[List, str, bytes]):
        result = []
        if isinstance(file, list):
            if len(file) == 1:
                result = file
            else:
                for item in file:
                    result.append(InputMediaVideo(media=item))
        else:
            result = [file]
        return Image(media=result)


@dataclass_json
@dataclass
class Audio:
    media: Union[str, BinaryIO] = field(default_factory=list)


@dataclass_json
@dataclass
class Document:
    media: Union[str, BinaryIO] = field(default_factory=list)


@dataclass_json
@dataclass
class Animation:
    media: Union[str, BinaryIO] = field(default_factory=list)


class Default:
    media = []
    keyboard = ReplyKeyboardRemove()


class Keyboard:
    def __init__(
            self,
            keyboard: List[List[Union[dict, str]]] = None,
            inline_mode: Optional[bool] = False,
    ):
        if not keyboard:
            self.keyboard = ReplyKeyboardRemove
        else:
            formatted_keyboard = []
            for _string in keyboard:
                if inline_mode:
                    keyboard_string = [
                        InlineKeyboardButton(**button)
                        for button in _string
                    ]
                else:
                    keyboard_string = [
                        KeyboardButton(**button)
                        if isinstance(button, dict)
                        else KeyboardButton(text=button)
                        for button in _string
                    ]
                formatted_keyboard.append(keyboard_string)
            if inline_mode:
                self.keyboard = InlineKeyboardMarkup(formatted_keyboard)
            else:
                self.keyboard = ReplyKeyboardMarkup(
                    keyboard=formatted_keyboard,
                    one_time_keyboard=True,
                    resize_keyboard=True,
                )
