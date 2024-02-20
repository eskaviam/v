# Copyright (c) 2022 Kyle Schouviller (https://github.com/kyle0654)


from invokeai.app.services.events.events_common import BaseEvent


class EventServiceBase:

    """Basic event bus, to have an empty stand-in when not needed"""

    def dispatch(self, event: BaseEvent) -> None:
        pass
