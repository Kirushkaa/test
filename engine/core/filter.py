import re
from typing import List

from telegram import Update, Message
from telegram.ext import BaseFilter, CallbackContext, Dispatcher


class UniFilter(BaseFilter):

    def __init__(
            self,
            bot_name: str,
            handler,
            phrases: List[str],
            file_types: List[str],
            state: List[str],
            dispatcher: Dispatcher,
    ):
        self.bot_name = bot_name
        self.phrases = phrases
        self.handler = handler
        self.file_types = file_types
        self.state = state
        self.dp = dispatcher

    name = None
    update_filter = True
    data_filter = False

    def filter(
            self,
            update: Update,
    ):
        user_id = update.message.to_dict()["from"]["id"]
        conclusion = {
            "state": False,
            "file_type": False,
            "phrase": False
        }
        context = CallbackContext.from_update(update, self.dp)
        data = update.to_dict()["message"]["from"]

        if not context.user_data.get(data["id"]):
            self.handler.collect_additional_context(context, update, self.dp, "_")

        if self.phrases == () or \
                (getattr(update.message, "caption") and self.check_for_regex(update.message.caption.lower(), self.phrases)) or \
                (getattr(update.message, "text") and self.check_for_regex(update.message.text.lower(), self.phrases)):
            conclusion["phrase"] = True
        if not conclusion["phrase"]:
            return False
        if not self.state or context.user_data[user_id]["state"] in self.state:
            conclusion["state"] = True
        if not conclusion["state"]:
            return False
        if self.file_types == ():
            if self.check_for_docs(update.message):
                conclusion["file_type"] = False
            else:
                conclusion["file_type"] = True
        elif self.file_types == ["any"]:
            conclusion["file_type"] = True
        else:
            for attr in self.file_types:
                if hasattr(update.message, attr) and getattr(update.message, attr) or \
                        (hasattr(update.message, "document") and getattr(update.message, "document")
                         and update.message.document.mime_type == attr):
                    conclusion["file_type"] = True
                    break
        if not conclusion["file_type"]:
            return False
        return True

    @staticmethod
    def check_for_docs(message: Message) -> bool:
        if hasattr(message, "document") and getattr(message, "document") or \
                hasattr(message, "photo") and getattr(message, "photo") or \
                hasattr(message, "audio") and getattr(message, "audio") or \
                hasattr(message, "voice") and getattr(message, "voice") or \
                hasattr(message, "video") and getattr(message, "video"):
            return True
        return False

    @staticmethod
    def check_for_regex(
            message: str,
            phrase_pool: list
    ) -> bool:
        for phrase in phrase_pool:
            if re.search(phrase.lower(), message):
                return True
        return False
