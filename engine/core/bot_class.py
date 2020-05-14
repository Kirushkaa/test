import logging
import os
import sys

from typing import Optional, Callable, List

from telegram import LabeledPrice, Update
from telegram.ext import (
    Updater, PreCheckoutQueryHandler, MessageHandler, Filters,
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
            inline_mode: bool = False,
            successful_payment: Optional[bool] = False
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
                inline_mode=inline_mode,
                successful_payment=successful_payment
            )
        return decorator

    def add_handlers(self):
        handlers_storage = sorted(
            UniHandler.handler_storage,
            key=lambda priority: priority[1],
            reverse=True
        )
        for handle in handlers_storage:
            self.dispatcher.add_handler(handle[0])
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

    def edit_message_processing(
            self,
            user_id: str,
            message_id: int,
            text: Optional[str] = "",
            image: Optional[Image] = Default,
            video: Optional[Video] = Default,
            audio: Optional[Audio] = Default,
            document: Optional[Document] = Default,
            animation: Optional[Animation] = Default,
            keyboard: Optional[Keyboard] = Default,
    ) -> None:

        if len(image.media + video.media) > 1 or\
                (image.media and len(image.media) > 1) or\
                (video.media and len(video.media) > 1):
            raise Exception('Sending more than 1 objects is not allowed')

        for media in [image.media, video.media, audio.media, animation.media, document.media]:
            if media:
                self.bot.edit_message_media(
                    chat_id=user_id,
                    message_id=message_id,
                    media=media,
                    caption=text,
                    reply_markup=keyboard.keyboard
                )
                self.bot.edit_message_caption(
                    chat_id=user_id,
                    message_id=message_id,
                    caption=text,
                    reply_markup=keyboard.keyboard
                )
                break
        else:
            self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=text,
                reply_markup=keyboard.keyboard
            )

    def id_counter(self) -> List:
        all_contexts = os.listdir(f"/tmp/{self.bot_name}/contexts")
        all_ids = [int(file.split(sep='.')[0]) for file in all_contexts]
        return all_ids

    def broadcast(
            self,
            user_ids: Optional[List] = None,
            message: Optional[str] = "",
            image: Optional[Image] = Default,
            video: Optional[Video] = Default,
            audio: Optional[Audio] = Default,
            document: Optional[Document] = Default,
            animation: Optional[Animation] = Default,
            keyboard: Optional[Keyboard] = Default,
    ) -> int:
        if user_ids is None:
            user_ids = self.id_counter()
        final_amount = 0
        for user in user_ids:
            try:
                self.response_processing(
                    user_id=user,
                    message=message,
                    image=image,
                    video=video,
                    audio=audio,
                    document=document,
                    animation=animation,
                    keyboard=keyboard
                )
                final_amount += 1
            except Exception as exc:
                self.bot.logger.warning(
                    f'Broadcast to user {str(user)} caused error {exc}'
                )
        return final_amount
