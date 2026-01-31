from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class CellSchema(BaseModel):
    id: int
    row_id: int
    period_id: int
    value: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class PeriodColumnSchema(BaseModel):
    id: int
    name: str
    order: int
    model_config = ConfigDict(from_attributes=True)

class RowSchema(BaseModel):
    id: int
    order: int
    level: int
    parent_id: Optional[int] = None
    entity: str
    article: str
    project: str
    cells: List[CellSchema]
    children: List['RowSchema'] = []  # Рекурсивная схема для дерева
    model_config = ConfigDict(from_attributes=True)

class TableData(BaseModel):
    periods: List[PeriodColumnSchema]  # Бывшие columns, теперь только периоды
    rows: List[RowSchema]
    
class RowCreate(BaseModel):
    parent_id: Optional[int] = None
    entity: str = ""
    article: str = ""
    project: str = ""

class CellUpdate(BaseModel):
    value: Optional[float] = None
