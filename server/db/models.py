import datetime
import enum
import logging
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import Column, String, DateTime, ForeignKey, \
    Integer, event, select, update,VARCHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import Connection
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import ChoiceType

from .base import Base
from .engine import Session

logger = logging.getLogger('uvicorn')


class ItemType(str, enum.Enum):
    FILE = 'FILE'
    FOLDER = 'FOLDER'


class SystemItem(Base):
    url = Column(VARCHAR(255), nullable=True,default=None)
    date = Column(DateTime(timezone=datetime.timezone.utc), nullable=False)
    type = Column(ChoiceType(ItemType, impl=String()), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('system_item.id'),
                       index=True, default=None,
                       nullable=True)
    size = Column(Integer, nullable=True)
    children: List['SystemItem'] = relationship(
        "SystemItem",
        backref=backref('parent', remote_side='SystemItem.id'),
        uselist=True, cascade="all, delete"
    )

    def get_child(self, index: int = 0) -> Optional["SystemItem"]:
        if len(self.children) > index:
            return self.children[index]
        return None

    def __str__(self):
        return f'{self.url} {self.type}'

    def __repr__(self):
        return f'<SystemItem {self.url}>'


@event.listens_for(SystemItem, 'after_insert')
def do_smth(mapper, connection: Connection, target):
    if target.parent_id is not None:
        session = Session()
        parent = session.query(SystemItem).filter_by(id=target.parent_id).one()
        parent.date = target.date
        session.add(parent)
        session.commit()


@event.listens_for(SystemItem, 'after_update')
def do_smth(mapper, connection: Connection, target: SystemItem):
    if target.parent_id is not None:
        session = Session()
        parent = session.query(SystemItem).filter_by(id=target.parent_id).one()
        parent.date = target.date
        session.add(parent)
        session.commit()


def calculate_category_price(category: SystemItem) -> \
        Optional[int]:
    """Рассчитывает суммарный размер всех элеметов"""
    count = 0
    stack = [[category, 0]]
    logger.info(stack)
    logger.warning('START CALCULATING')
    while len(stack):
        logger.info(stack)
        last, index = stack[-1]
        stack[-1][1] += 1
        child = last.get_child(index)
        if child and child.type == ItemType.FILE:
            count += child.size
        elif child:
            stack.append([child, 0])
        else:
            stack.pop()
    if count:
        return count
    return None
