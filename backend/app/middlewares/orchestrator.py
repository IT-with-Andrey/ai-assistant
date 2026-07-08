from typing import List
from .base import BaseMiddleware, ChatContext

class ChatOrchestrator:
    def __init__(self, middlewares: List[BaseMiddleware]):
        self.middlewares = middlewares

    async def run(self, ctx: ChatContext) -> ChatContext:
        for mw in self.middlewares:
            ctx = await mw.process(ctx)
            if ctx.should_stop:
                break
        return ctx