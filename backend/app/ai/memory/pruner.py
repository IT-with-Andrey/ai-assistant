
from typing import List , Dict , Any

from backend.app.ai.memory.base import BaseHistoryPruner

from backend.app.core.logger import logger


class ByteSizeHistoryPruner(BaseHistoryPruner):
    """Отрезает старые сообщения, если история превышает лимит в байтах"""
    def prune(self , history : List[Dict[str, Any]], max_bytes: int = 4000 ) -> List[Dict[str,Any]]:
        pruned_history = []
        current_bytes = 0 

        for message in reversed(history):
            msg_content = message.get('content',"")
            msg_bytes = len(msg_content.encode('utf-8'))
            if current_bytes + msg_bytes > max_bytes:
                logger.info(f' История обрезанна по байтовому лимиту {max_bytes}')
                break

            current_bytes +=msg_bytes
            pruned_history.insert(0, message)
        return pruned_history
