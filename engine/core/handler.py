import os

import json
from pathlib import Path
from typing import Callable, List, Optional
from telegram.ext import MessageHandler, Dispatcher, Filters

from engine.core.filter import UniFilter


class UniHandler(MessageHandler):
    handler_storage = []

    def __init__(
            self,
            callback_func: Callable,
            dispatcher: Dispatcher,
            bot_name: str,
            file_types: List[str],
            faq_json_path: Optional[str],
            similarity_score: float,
            phrases: List[str],
            state: list,
            priority: int,
            inline_mode: bool,
            successful_payment: Optional[bool]
    ):
        self.bot_name = bot_name
        self.handler_payload = {}
        self.filter = UniFilter(
            bot_name=bot_name,
            handler=self,
            phrases=phrases,
            faq_json_path=faq_json_path,
            similarity_score=similarity_score,
            file_types=file_types,
            state=state,
            inline_mode=inline_mode,
            dispatcher=dispatcher,
        )
        if successful_payment:
            super().__init__(
                filters=Filters.successful_payment,
                callback=callback_func
            )
        else:
            super().__init__(
                filters=self.filter,
                callback=callback_func
            )

        UniHandler.handler_storage.append((self, priority))

    def handle_update(self, update, dispatcher, check_result, context=None):
        self.collect_additional_context(context, update, dispatcher, check_result)
        if update.message:
            user_id = update.message.to_dict()["from"]["id"]
        elif update.callback_query:
            user_id = update.callback_query.to_dict()["from"]["id"]
        else:
            print("Unexpected update")
            return
        final_update = update.to_dict()
        final_update["handler_payload"] = self.handler_payload
        return self.callback(final_update, context.user_data[user_id])

    def update_file_context(self, context: dict):
        with open(
                Path(f"/tmp/{self.bot_name}/contexts") / f"{context['user_data']['id']}.json",
                "w",
                encoding='utf-8'
        ) as file:
            file.write(json.dumps(context))

    def collect_additional_context(self, context, update, dispatcher, check_result):
        if not os.path.exists(Path(f"/tmp/{self.bot_name}")):
            os.mkdir(Path(f"/tmp/{self.bot_name}"))
            os.mkdir(Path(f"/tmp/{self.bot_name}/contexts"))
        data = update.to_dict()["message"]["from"]
        if not context.user_data.get(data["id"]):
            context.user_data[data["id"]] = {
                "id": data["id"],
                "user_data": data,
                "state": '',
                "payload": {},
            }

        self.update_file_context(context.user_data[data["id"]])
