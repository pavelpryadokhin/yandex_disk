import datetime
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from .schemas.system_item import SystemItemImportRequest, SystemItemHistoryUnit, SystemItemHistoryResponse
from sqlalchemy.orm import Session
from db.engine import get_session
from db.models import SystemItem, ItemType
# from server.db.engine import get_session
# from server.db.models import SystemItem, ItemType
from starlette.responses import Response
from loguru import logger
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, \
    HTTP_404_NOT_FOUND
from .schemas.response import HTTP_400_RESPONSE, HTTP_404_RESPONSE

router = APIRouter()


@router.get('/test', name='test', tags=['тест. роут'])
def get_test() -> Dict[str, str]:
    """Тестовый метод для проверки запуска приложения"""
    return {'status': 'ok'}


@router.post('/imports', name='Импортирует элементы файловой системы',
             status_code=200, tags=['Базовые задачи'])
def import_items(items: SystemItemImportRequest, session: Session = Depends(
    get_session)) -> Response:
    for systemitem in items.items:
        systemitem.date = items.update_date
        systemitemmodel = session.query(SystemItem).filter(SystemItem.id ==
                                                           systemitem.id).one_or_none()

        if systemitemmodel is not None:
            logger.warning('find systemitem')
            if systemitemmodel.type != systemitem.type:
                raise HTTPException(status_code=400, detail='Validation Failed')
            for var, value in vars(systemitem).items():
                setattr(systemitemmodel, var, value) if value else None
            session.add(systemitemmodel)
        else:
            session.add(SystemItem(**systemitem.dict()))
        session.commit()
    return Response(status_code=200)


@router.delete('/delete/{id}', name='Удалить элемент по идентификатору',
               status_code=200, responses={200: {'description': 'Удаление прошло успешно.',
                                                 'model': None},
                                           HTTP_400_BAD_REQUEST: HTTP_400_RESPONSE,
                                           HTTP_404_NOT_FOUND: HTTP_404_RESPONSE,
                                           }, tags=['Базовые задачи'])
def delete_item(id: str, sesion: Session = Depends(get_session)) -> Response:
    """        Удалить элемент по идентификатору. При удалении папки удаляются 
    все дочерние элементы. Доступ к истории обновлений удаленного элемента 
    невозможен.
    """
    systemitem = sesion.query(SystemItem).filter_by(id=id).one_or_none()
    if systemitem is None:
        raise HTTPException(status_code=404, detail='Item not found')
    try:
        sesion.delete(systemitem)
        sesion.commit()
        return Response(status_code=HTTP_200_OK)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=400, detail='Validation Failed')


@router.get('/nodes/{id}/',
            name='Получить информацию об элементе по идентификатору.',
            response_model=SystemItemHistoryUnit, response_model_by_alias=True,
            tags=['Базовые задачи'])
def get_item(id: str, session: Session = Depends(get_session)):
    '''Получить информацию об элементе по идентификатору.
     При получении информации о папке также предоставляется
      информация о её дочерних элементах.
    '''
    systemitem = sesion.query(SystemItem).filter_by(id=id).one_or_none()
    if systemitem is None:
        raise HTTPException(status_code=404, detail='Item not found')
    se: SystemItemHistoryUnit = SystemItemHistoryUnit.from_orm(systemitem)
    if se.type == ItemType.FOLDER:
        stack = [[se, 0, 0]]
        while len(stack):
            last, index = stack[-1][0], stack[-1][1]
            child = last.get_child(index)
            if child is None:
                last.size = stack[-1][2]
                if len(stack) > 1:
                    stack[-2][2] += stack[-1][2]
                stack.pop()
            else:
                stack[-1][1] += 1
                if child.type == ItemType.FILE:
                    stack[-1][2] += child.size
                else:
                    stack.append([child, 0, 0])
    return se


@router.get('/sales', status_code=200, tags=['Дополнительные задачи'],
            response_model=SystemItemHistoryResponse)
def get_sales(date: datetime.datetime, session: Session = Depends(get_session)) -> SystemItemHistoryResponse:
    '''
    Получение списка **файлов**,
    которые были обновлены за последние 24 часа включительно
    '''
    logger.info(date)
    items = session.query(SystemItem).filter(SystemItem.type == ItemType.FILE,
                                             SystemItem.date <= date,
                                             SystemItem.date >= date - datetime.timedelta(days=1)).all()
    return  SystemItemHistoryResponse(items=items)
