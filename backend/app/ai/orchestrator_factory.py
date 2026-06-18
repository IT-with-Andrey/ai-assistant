
# Правильные пути
from backend.app.middlewares.orchestrator import ChatOrchestrator
from backend.app.ai.provider_router import ProviderRouter
from backend.app.ai.providers.gemini_provider import GeminiProvider
from backend.app.ai.providers.ollama_provider import OllamaProvider
from backend.app.ai.memory_orchestrator import MemoryOrchestrator
from backend.app.ai.memory.mem0_storage import Mem0StorageProvider
from backend.app.ai.memory.pruner import ByteSizeHistoryPruner
from backend.app.ai.memory.optimizer import MockMemoryOptimizer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.middlewares.command_handler import CommandHandlerMiddleware
from backend.app.middlewares.save_user_message import SaveUserMessageMiddleware
from backend.app.middlewares.save_assistant_message import SaveAssistantMessageMiddleware
from backend.app.middlewares.load_history import LoadHistoryMiddleware
from backend.app.middlewares.search_memory import SearchMemoryMiddleware
from backend.app.middlewares.context_assembly import ContextAssemblyMiddleware
from backend.app.middlewares.call_llm import CallLLMMiddleware

from backend.app.middlewares.streaming_call_llm import StreamingCallLLMMiddleware
from backend.app.ai.memory.manager import MemoryManager
from backend.app.ai.memory.episodic import EpisodicMemory
from backend.app.ai.memory.reflection import ReflectionLayer
from backend.app.ai.memory.middleware import MemoryManagerMiddleware
class AppContainer:
    def __init__(self):
        # Память
        self.memory_storage = Mem0StorageProvider()
        self.history_pruner = ByteSizeHistoryPruner()
        self.memory_optimizer = MockMemoryOptimizer()
        self.memory_orchestrator = MemoryOrchestrator(
            vector_memory=self.memory_storage,
            pruner=self.history_pruner,
            optimizer=self.memory_optimizer
        )
        # Провайдеры (только Gemini, Ollama отключена, т.к. модель сломана)
                # Провайдеры
        self.gemini_provider = GeminiProvider()
        self.ollama_provider = OllamaProvider(model_name="gemma4:31b-cloud")
        self.llm_router = ProviderRouter(providers=[self.ollama_provider, self.gemini_provider])
        # 3. НОВЫЕ КОМПОНЕНТЫ: Продвинутая память (Эпизоды, Рефлексия, Менеджер)
        self.episodic_memory = EpisodicMemory(self.memory_orchestrator)
        
        self.memory_manager = MemoryManager(
            llm_provider=self.llm_router,
            memory_orchestrator=self.memory_orchestrator,
            episodic_memory=self.episodic_memory
        )
        
        self.reflection_layer = ReflectionLayer(
            llm_provider=self.llm_router,
            memory_orchestrator=self.memory_orchestrator,
            episodic_memory=self.episodic_memory
        )

app_container = AppContainer()



def create_chat_orchestrator(db: AsyncSession, background_tasks=None) -> ChatOrchestrator:
    middlewares = [
        CommandHandlerMiddleware(app_container.memory_orchestrator),
        SaveUserMessageMiddleware(db),          
        LoadHistoryMiddleware(db),              
        SearchMemoryMiddleware(app_container.memory_orchestrator),
        ContextAssemblyMiddleware(),
        CallLLMMiddleware(app_container.llm_router),
        SaveAssistantMessageMiddleware(db),     
        
        MemoryManagerMiddleware(app_container.memory_manager, background_tasks=background_tasks)
    ]
    return ChatOrchestrator(middlewares)


def create_streaming_orchestrator(db: AsyncSession, background_tasks=None) -> ChatOrchestrator:
    middlewares = [
        CommandHandlerMiddleware(app_container.memory_orchestrator),
        SaveUserMessageMiddleware(db),
        LoadHistoryMiddleware(db),
        SearchMemoryMiddleware(app_container.memory_orchestrator),
        ContextAssemblyMiddleware(),

        StreamingCallLLMMiddleware(app_container.llm_router),
        
        MemoryManagerMiddleware(app_container.memory_manager, background_tasks=background_tasks)
    ]
    return ChatOrchestrator(middlewares)