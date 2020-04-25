import logging
import os
import sys

from typing import Optional, Callable, List

from telegram.ext import (
    Updater,
)

from telegram.error import BadRequest

from engine.config import ERROR
from .handler import UniHandler
from .content import (
    Image,
    Video,
    Audio,
    Document,
    Keyboard, Animation, Default
)


class TelegramBot(Updater):

    def __init__(
            self,
            token: str,
            use_context: bool,
            bot_name: str,
            dev_mode: Optional[str] = "n",
            request_kwargs: Optional[dict] = None,
    ):
        super().__init__(
            token=token,
            use_context=use_context,
            request_kwargs=request_kwargs
        )

        logging_level = logging.DEBUG if dev_mode == "y" else logging.INFO
        self.bot_name = bot_name
        self.logger = logging.getLogger()
        self.logger.setLevel(logging_level)
        self.formatter = logging.Formatter("%(asctime)s %(message)s")

        self.debug_logger = logging.StreamHandler(sys.stdout)
        self.debug_logger.setLevel(logging_level)
        self.debug_logger.setFormatter(self.formatter)
        self.logger.addHandler(self.debug_logger)

        self.file_handler_logger = logging.FileHandler(
            f"{os.curdir}/logs/{self.bot_name}.log",
            encoding="utf8"
        )
        self.file_handler_logger.setFormatter(self.formatter)
        self.file_handler_logger.setLevel(logging_level)
        self.logger.addHandler(self.file_handler_logger)
        self.dispatcher.add_error_handler(self.error)

    def bot_handler(
            self,
            phrases: List[str] = (),
            file_types: List[str] = (),
            state: List[str] = None,
            priority: int = 0,
    ):

        def decorator(func: Callable):
            return UniHandler(
                callback_func=func,
                dispatcher=self.dispatcher,
                bot_name=self.bot_name,
                phrases=phrases,
                file_types=file_types,
                state=state,
                priority=priority,
            )

        return decorator

    def add_handlers(self):
        handlers_storage = UniHandler.handler_list
        for handle in handlers_storage:
            self.dispatcher.add_handler(handle)
        self.bot.logger.warning('Start polling')

    def error(self, update, context) -> None:
        """Log Errors caused by Updates."""
        self.bot.logger.warning('Update "%s" caused error "%s"', update, context.error)
        update.message.reply_text(ERROR)

    def response_processing(
            self,
            user_id: str,
            message: Optional[str] = "",
            image: Optional[Image] = Default,
            video: Optional[Video] = Default,
            audio: Optional[Audio] = Default,
            document: Optional[Document] = Default,
            animation: Optional[Animation] = Default,
            keyboard: Optional[Keyboard] = Default,
    ) -> None:
        if len(image.media + video.media) > 10 or\
                (image.media and len(image.media) > 10) or\
                (video.media and len(video.media) > 10):
            raise Exception('Sending more than 10 objects is not allowed')
        if 1 < len(image.media + video.media) <= 10 or \
                (image.media and 1 < len(image.media) <= 10) or \
                (video.media and 1 < len(video.media) <= 10):
            if len(image.media + video.media) <= 10:
                self.bot.send_media_group(
                    chat_id=user_id,
                    media=(image.media + video.media),
                )
                self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    reply_markup=keyboard.keyboard
                )

        elif image.media:
            self.bot.send_photo(
                chat_id=user_id,
                photo=image.media[0],
                caption=message,
                reply_markup=keyboard.keyboard
            )
        elif video.media:
            self.bot.send_video(
                chat_id=user_id,
                video=video.media[0],
                caption=message,
                reply_markup=keyboard.keyboard
            )
        elif audio.media:
            self.bot.send_audio(
                chat_id=user_id,
                audio=audio.media,
                caption=message,
                reply_markup=keyboard.keyboard
            )
        elif animation.media:
            self.bot.send_animation(
                chat_id=user_id,
                animation=animation.media,
                caption=message,
                reply_markup=keyboard.keyboard
            )
        elif document.media:
            self.bot.send_document(
                chat_id=user_id,
                document=document.media,
                caption=message,
                reply_markup=keyboard.keyboard
            )
        else:
            self.bot.send_message(
                chat_id=user_id,
                text=message,
                reply_markup=keyboard.keyboard
            )

    def id_counter(self) -> List:
        all_contexts = os.listdir(f"/tmp/{self.bot_name}/contexts")
        all_ids = [int(file.split(sep='.')[0]) for file in all_contexts]
        return all_ids

    def broadcast(
            self,
            users_id: Optional[List] = 0,
            message: Optional[str] = "",
            image: Optional[Image] = Default(),
            video: Optional[Video] = Default(),
            audio: Optional[Audio] = Default(),
            document: Optional[Document] = Default(),
            animation: Optional[Animation] = Default(),
            keyboard: Optional[Keyboard] = None,
    ) -> None:
        if not users_id:
            users_id = self.id_counter()
        for user in users_id:
            try:
                self.bot.response_processing(
                    user_id=user,
                    message=message,
                    image=image,
                    video=video,
                    audio=audio,
                    document=document,
                    animation=animation,
                    keyboard=keyboard
                )
            except BadRequest:
                self.bot.logger.warning(
                    f'Broadcast to user {str(user)} caused error {BadRequest.__text_signature__}'
                )
            except:
                self.bot.logger.warning(
                    f'Broadcast to user {str(user)} caused unknown error'
                )
