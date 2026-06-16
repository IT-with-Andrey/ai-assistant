from .base import BaseMiddleware, ChatContext
from backend.app.ai.persona_manager import PersonaManager
from backend.app.core.logger import logger
class CommandHandlerMiddleware(BaseMiddleware):
    def __init__(self, memory_orchestrator):
        self.memory_orchestrator = memory_orchestrator

    async def process(self, ctx: ChatContext) -> ChatContext:
        logger.debug("CommandHandlerMiddleware: начало обработки")
        user_input = ctx.user_input.strip()
        if not user_input.startswith("/"):
            logger.debug("CommandHandlerMiddleware: команда /help выполнена")
            return ctx

        if user_input.startswith("/role"):
            parts = user_input.split(" ", 1)
            if len(parts) < 2 or not PersonaManager.validate_role(parts[1]):
                roles = "\n".join(
                    [f"- {r['id']} ({r['display_name']})" for r in PersonaManager.get_available_roles()])
                ctx.response = f"Неверная роль. Доступные роли:\n{roles}"
            else:
                new_role = parts[1]
                await self.memory_orchestrator.add_user_memory(ctx.user_id, text=f"assistant_role: {new_role}")
                ctx.response = f"Роль успешно сменена на: {new_role}"
            ctx.should_stop = True
            return ctx

        if user_input.startswith("/help"):
            ctx.response = "Доступные команды:\n/role <название> - сменить роль\n/help - список команд"
            ctx.should_stop = True
            logger.debug("CommandHandlerMiddleware: не команда, пропускаем")
            return ctx

        return ctx