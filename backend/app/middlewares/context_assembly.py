from .base import BaseMiddleware, ChatContext
from backend.app.ai.context_builder import build_context

class ContextAssemblyMiddleware(BaseMiddleware):
    async def process(self, ctx: ChatContext) -> ChatContext:
        # 🔥 ХИТРЫЙ ХОД: Импортируем контейнер локально внутри метода!
        # Это полностью предотвращает циклическую зависимость (Circular Import) при старте Uvicorn
        from backend.app.ai.orchestrator_factory import app_container

        ctx.llm_context = await build_context(
        history=ctx.history,
        user_input=ctx.user_input,
        memory_orchestrator=app_container.memory_orchestrator,
        user_facts=ctx.facts,
        user_id=ctx.user_id,
        persona_id=ctx.persona_id       # <-- новая строка
    )
        return ctx