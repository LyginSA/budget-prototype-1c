from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from app.database import get_db
from app.models import PeriodColumn, Row, Cell
from app.schemas import TableData, PeriodColumnSchema, RowSchema, CellSchema, RowCreate
from app.services.exchange_1c import Exchange1CService

router = APIRouter(prefix="/api/table", tags=["table"])

async def build_tree(rows: list, parent_id: Optional[int] = None) -> List[RowSchema]:
    """Рекурсивно строим дерево строк"""
    result = []
    for row in rows:
        if row.parent_id == parent_id:
            children = await build_tree(rows, row.id)
            cells = [CellSchema.model_validate(c) for c in row.cells]
            result.append(RowSchema(
                id=row.id,
                order=row.order,
                level=row.level,
                parent_id=row.parent_id,
                entity=row.entity,
                article=row.article,
                project=row.project,
                cells=cells,
                children=children
            ))
    return result

@router.get("/", response_model=TableData)
async def get_table(db: AsyncSession = Depends(get_db)):
    """Получить таблицу с иерархией строк и периодами"""
    # Загружаем периоды (бывшие колонки)
    periods_result = await db.execute(select(PeriodColumn).order_by(PeriodColumn.order))
    periods = periods_result.scalars().all()
    
    # Загружаем все строки с ячейками
    rows_result = await db.execute(select(Row).order_by(Row.order))
    rows = rows_result.scalars().all()
    
    # Подгружаем ячейки для каждой строки
    for row in rows:
        await db.refresh(row, ['cells'])
    
    # Строим дерево (только корневые элементы parent_id=None)
    tree = await build_tree(rows, None)
    
    return TableData(
        periods=[PeriodColumnSchema.model_validate(p) for p in periods],
        rows=tree
    )

@router.post("/init")
async def init_table(db: AsyncSession = Depends(get_db)):
    """Инициализация примера из Excel (3 периода, 2 строки с подстроками)"""
    # Проверяем, есть ли уже данные
    result = await db.execute(select(PeriodColumn))
    if result.scalars().first():
        return {"message": "Таблица уже инициализирована"}
    
    # Создаем 3 периода (как в примере: 45658, 45689, 45717...)
    period_names = ["45658", "45689", "45717", "45748", "45778"]
    periods = []
    for i, name in enumerate(period_names):
        p = PeriodColumn(name=name, order=i)
        db.add(p)
        periods.append(p)
    
    await db.flush()
    
    # Создаем корневую строку (уровень 0)
    root_row = Row(
        order=0, 
        level=0, 
        entity="ИКС", 
        article="CS0198234", 
        project="M5"
    )
    db.add(root_row)
    await db.flush()
    
    # Создаем подстроки (уровень 1)
    child1 = Row(
        order=1,
        level=1,
        parent_id=root_row.id,
        entity="",
        article="",
        project="Обслуживание патрубков"
    )
    db.add(child1)
    await db.flush()
    
    child2 = Row(
        order=2,
        level=1,
        parent_id=root_row.id,
        entity="",
        article="",
        project="1 кол-во дгу"
    )
    db.add(child2)
    await db.flush()
    
    # Создаем ячейки для всех строк
    for row in [root_row, child1, child2]:
        for period in periods:
            cell = Cell(row_id=row.id, period_id=period.id, value=None)
            db.add(cell)
    
    await db.commit()
    return {"message": "Создана структура как в примере Excel"}

@router.post("/periods", response_model=PeriodColumnSchema)
async def add_period(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Добавить новый период (колонку с числами)"""
    result = await db.execute(select(PeriodColumn).order_by(PeriodColumn.order.desc()))
    last = result.scalars().first()
    new_order = (last.order + 1) if last else 0
    new_name = name or f"Период {new_order + 1}"
    
    period = PeriodColumn(name=new_name, order=new_order)
    db.add(period)
    await db.flush()
    
    # Добавляем пустые ячейки для всех существующих строк
    rows_result = await db.execute(select(Row))
    rows = rows_result.scalars().all()
    for row in rows:
        cell = Cell(row_id=row.id, period_id=period.id, value=None)
        db.add(cell)
    
    await db.commit()
    await Exchange1CService.notify_period_added(new_name)
    
    return PeriodColumnSchema.model_validate(period)

@router.delete("/periods/{period_id}")
async def delete_period(period_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить период"""
    period = await db.get(PeriodColumn, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Период не найден")
    
    await db.delete(period)
    await db.commit()
    await Exchange1CService.notify_structure_changed("period_deleted", {"id": period_id})
    return {"message": "Период удален"}

@router.post("/rows", response_model=RowSchema)
async def add_row(row_data: RowCreate, db: AsyncSession = Depends(get_db)):
    """Добавить строку (корневую или подстроку)"""
    # Определяем уровень вложенности
    level = 0
    if row_data.parent_id:
        parent = await db.get(Row, row_data.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Родительская строка не найдена")
        level = parent.level + 1
    
    # Максимальный order
    result = await db.execute(select(Row).order_by(Row.order.desc()))
    last = result.scalars().first()
    new_order = (last.order + 1) if last else 0
    
    row = Row(
        order=new_order,
        level=level,
        parent_id=row_data.parent_id,
        entity=row_data.entity or "",
        article=row_data.article or "",
        project=row_data.project or ""
    )
    db.add(row)
    await db.flush()
    
    # Создаем ячейки для всех периодов
    periods_result = await db.execute(select(PeriodColumn))
    periods = periods_result.scalars().all()
    for period in periods:
        cell = Cell(row_id=row.id, period_id=period.id, value=None)
        db.add(cell)
    
    await db.commit()
    await Exchange1CService.notify_row_added({
        "id": row.id,
        "entity": row.entity,
        "article": row.article,
        "project": row.project,
        "parent_id": row.parent_id
    })
    
    # Возвращаем с пустыми children
    return RowSchema(
        id=row.id,
        order=row.order,
        level=row.level,
        parent_id=row.parent_id,
        entity=row.entity,
        article=row.article,
        project=row.project,
        cells=[CellSchema.model_validate(c) for c in row.cells],
        children=[]
    )

@router.put("/rows/{row_id}")
async def update_row_fields(
    row_id: int, 
    entity: Optional[str] = None,
    article: Optional[str] = None,
    project: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Обновить текстовые поля строки (Юрлицо, Статья, Проект)"""
    row = await db.get(Row, row_id)
    if not row:
        raise HTTPException(status_code=404, detail="Строка не найдена")
    
    if entity is not None:
        row.entity = entity
    if article is not None:
        row.article = article
    if project is not None:
        row.project = project
    
    await db.commit()
    await Exchange1CService.notify_row_updated(row_id, {
        "entity": row.entity,
        "article": row.article,
        "project": row.project
    })
    
    return {"message": "Поля обновлены"}

@router.delete("/rows/{row_id}")
async def delete_row(row_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить строку (каскадно удалит подстроки и ячейки)"""
    row = await db.get(Row, row_id)
    if not row:
        raise HTTPException(status_code=404, detail="Строка не найдена")
    
    await db.delete(row)
    await db.commit()
    await Exchange1CService.notify_structure_changed("row_deleted", {"id": row_id})
    return {"message": "Строка удалена"}

@router.put("/cells/{row_id}/{period_id}", response_model=CellSchema)
async def update_cell(
    row_id: int,
    period_id: int,
    value: Optional[float] = None,
    db: AsyncSession = Depends(get_db)
):
    """Обновить значение ячейки (число для периода)"""
    result = await db.execute(
        select(Cell).where(Cell.row_id == row_id, Cell.period_id == period_id)
    )
    cell = result.scalar_one_or_none()
    
    if not cell:
        cell = Cell(row_id=row_id, period_id=period_id, value=value)
        db.add(cell)
    else:
        cell.value = value
    
    await db.commit()
    await db.refresh(cell)
    await Exchange1CService.notify_cell_updated(row_id, period_id, value)
    
    return CellSchema.model_validate(cell)
