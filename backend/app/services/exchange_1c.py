import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Exchange1CService:
    @staticmethod
    async def notify_row_added(row_data: Dict[str, Any]):
        """
        TODO: Интеграция с 1С - добавление строки бюджета
        Отправка данных: entity (юрлицо), article (статья), project (проект), 
        parent_id (родительская строка для иерархии)
        """
        logger.info(f"[1С-STUB] Добавлена строка бюджета: {row_data}")
        pass

    @staticmethod
    async def notify_row_updated(row_id: int, data: Dict[str, Any]):
        """
        TODO: Интеграция с 1С - изменение фиксированных полей (Юрлицо, Статья, Проект)
        """
        logger.info(f"[1С-STUB] Обновлена строка {row_id}: {data}")
        pass

    @staticmethod
    async def notify_cell_updated(row_id: int, period_id: int, value: Optional[float]):
        """
        TODO: Интеграция с 1С - изменение значения по периоду
        Период (месяц) = {period_id}, значение = {value}
        """
        logger.info(f"[1С-STUB] Обновлено значение периода: строка={row_id}, период={period_id}, значение={value}")
        pass

    @staticmethod
    async def notify_period_added(period_name: str):
        """
        TODO: Интеграция с 1С - добавление нового периода (месяца)
        """
        logger.info(f"[1С-STUB] Добавлен период: {period_name}")
        pass

    @staticmethod
    async def notify_structure_changed(change_type: str, details: Dict[str, Any]):
        """
        TODO: Общее уведомление об изменении структуры (удаление строк/периодов)
        """
        logger.info(f"[1С-STUB] Изменение структуры: {change_type} - {details}")
        pass
