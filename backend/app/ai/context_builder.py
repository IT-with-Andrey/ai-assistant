from backend.app.ai.persona_manager import PersonaManager
from backend.app.core.logger import logger

# 🔥 ИСПРАВЛЕНО: Никаких импортов app_container сверху! Полная изоляция от фабрики.

async def build_context(history, user_input, memory_orchestrator, summary: str = None, user_facts: str = None, user_id: str = 'default_user'):
    
    # Теперь memory_orchestrator заходит честно снаружи как аргумент функции
    persona_manager = PersonaManager(memory_orchestrator)
    facts = await memory_orchestrator.get_user_fact(user_id)
    
    role = 'default'
    for fact in facts:
        if isinstance(fact, str) and fact.startswith('assistant_role:'):
            role = fact.split(':', 1)[1].strip()
            break

    system_prompt = await persona_manager.get_system_prompt(role)

    message = []
    last_msg = history[-1] if history else None
    if isinstance(last_msg, dict):
        last_is_system = last_msg.get('role') == 'system'
        last_content = last_msg.get('content') if last_is_system else None
    else:
        last_is_system = last_msg and hasattr(last_msg, 'role') and last_msg.role == 'system'
        last_content = last_msg.content if last_is_system else None

    if not last_is_system or last_content != system_prompt:
        message.append({"role": "system", "content": system_prompt})
    if user_facts:
        message.append({"role": "system", "content": f"Факты о пользователе:\n{user_facts}"})

    if summary:
        message.append({"role": "system", "content": f"Контекст предыдущего диалога:\n{summary}"})

    clean_history = []
    for m in history:
        if hasattr(m, 'role'):
            role_h = m.role
            content = m.content
        else:
            role_h = m['role']
            content = m['content']
        clean_history.append({'role': role_h, 'content': str(content)})

    message.extend(clean_history)
    message.append({"role": "user", "content": str(user_input)})
    logger.debug("ИТОГОВЫЙ КОНТЕКСТ ДЛЯ LLM: %s...", str(message)[:300])
    logger.debug("КОЛИЧЕСТВО СООБЩЕНИЙ В КОНТЕКСТЕ: %d", len(message))
    return message