import json
import re
import numpy as np


from pathlib import Path

from datetime import datetime
from typing import List, Optional, Dict

from sklearn.metrics.pairwise import cosine_similarity

from engine.faq_models.vectorizer import Vectorizer

from telegram import Update, Message, Chat
from telegram.ext import BaseFilter, CallbackContext, Dispatcher


class UniFilter(BaseFilter):

    def __init__(
            self,
            bot_name: str,
            handler,
            phrases: List[str],
            faq_json_path: Optional[str],
            similarity_score: float,
            file_types: List[str],
            state: List[str],
            inline_mode: bool,
            dispatcher: Dispatcher,
    ):
        self.vectorizer = Vectorizer.model
        self.faq_json_path = faq_json_path
        if self.faq_json_path is not None:
            with open(str(Path.cwd().absolute() / Path(self.faq_json_path)), "r+") as f:
                self.faq_dict: Dict = json.load(f)

            for key in self.faq_dict.keys():
                self.faq_dict[key]["vectors"] = self.vectorizer.encode(
                    self.faq_dict[key]["phrases"])

        self.similarity_score = similarity_score
        self.bot_name = bot_name
        self.phrases = phrases
        self.handler = handler
        self.file_types = file_types
        self.state = state
        self.dp = dispatcher
        self.inline_mode = inline_mode

    name = None
    update_filter = True
    data_filter = False

    def filter(self, update: Update):
        if not update.message and not update.callback_query:
            return False

        conclusion = {
            "state": False,
            "file_type": False,
            "phrase": False,
        }
        context = CallbackContext.from_update(update, self.dp)

        if self.inline_mode:
            if update.callback_query:
                data = update.to_dict()["callback_query"]["from"]
                update.message = Message(
                    chat=Chat(id=update.callback_query.chat_instance, type='private'),
                    date=datetime.today(),
                    from_user=update.callback_query.from_user,
                    message_id=update.callback_query.id,
                    text=update.callback_query.data,
                )
            else:
                return False
        else:
            if update.callback_query:
                return False
            data = update.to_dict()["message"]["from"]

        if not context.user_data.get(data["id"]):
            self.handler.collect_additional_context(context, update, self.dp, "_")

        if getattr(update.message, "caption"):
            mess = update.message.caption.lower()
        elif getattr(update.message, "text"):
            mess = update.message.text.lower()
        else:
            mess = None

        if mess is not None and self.phrases == () or self.check_for_regex(mess, self.phrases):
            conclusion["phrase"] = True

        if mess is not None and self.faq_json_path:
            faq_options = []
            message_vector = self.vectorizer.encode([mess])
            for key in self.faq_dict.keys():
                max_score = np.max(cosine_similarity(message_vector, self.faq_dict[key]["vectors"]))
                if max_score > self.similarity_score:
                    conclusion["phrase"] = True
                    faq_options.append(
                        (key, {
                            "phrases": self.faq_dict[key]["phrases"],
                            "answer": self.faq_dict[key]["answer"],
                            "metadata": self.faq_dict[key]["metadata"]
                        }, max_score)
                    )
            if faq_options:
                faq_options.sort(key=lambda x: x[2], reverse=True)
                self.handler.handler_payload.update({"faq_answer": faq_options})
            else:
                conclusion["phrase"] = False

        if not conclusion["phrase"]:
            return False
        if not self.state or context.user_data[data["id"]]["state"] in self.state:
            conclusion["state"] = True
        if not conclusion["state"]:
            return False
        if self.file_types == ():
            conclusion["file_type"] = False if self.check_for_docs(update.message) else True
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
