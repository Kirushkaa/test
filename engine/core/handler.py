import json
from pathlib import Path
from typing import Callable, List

from telegram.ext import MessageHandler, Dispatcher

from engine.core.filter import UniFilter


class UniHandler(MessageHandler):
    handler_list = []

    def __init__(
            self,
            callback_func: Callable,
            dispatcher: Dispatcher,
            bot_name: str,
            file_types: List[str] = (),
            phrases: List[str] = (),
            state: list = None,
            priority: int = 0,
    ):
        self.bot_name = bot_name
        self.filter = UniFilter(
                bot_name=bot_name,
                handler=self,
                phrases=phrases,
                file_types=file_types,
                state=state,
                priority=priority,
                dispatcher=dispatcher
            )
        super().__init__(
            filters=self.filter,
            callback=callback_func
        )

        UniHandler.handler_list.append(self)

    def handle_update(self, update, dispatcher, check_result, context=None):
        self.collect_additional_context(context, update, dispatcher, check_result)
        user_id = update.message.to_dict()["from"]["id"]
        # TODO context = context[user], remove user_id
        return self.callback(update.message.to_dict(), context.user_data[user_id])

    def update_file_context(self, new_context: dict):
        with open(Path(f"/tmp/{self.bot_name}/contexts") / f"{new_context['user_data']['id']}.json",
                  "w",
                  encoding='utf-8') as file:
            file.write(json.dumps(new_context))

    def collect_additional_context(self, context, update, dispatcher, check_result):
        data = update.to_dict()["message"]["from"]
        if not context.user_data.get(data["id"]):
            context.user_data[data["id"]] = {
                "id": data["id"],
                "user_data": data,
                "state": '',
                "payload": [],
            }

        self.update_file_context(context.user_data[data["id"]])
