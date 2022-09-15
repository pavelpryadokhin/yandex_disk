from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator, root_validator
from db.models import ItemType
# from server.db.models import ItemType

from typing import Optional, List


def datetime_format(dt: datetime) -> str:
    return dt.isoformat(timespec='milliseconds', ).replace('+00:00', 'Z')


class SystemItemType(BaseModel):
    id: str
    url: Optional[str] = None
    date: Optional[datetime]
    parent_id: Optional[str] = Field(alias='parentId')
    size: Optional[int]
    type: ItemType

    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
        orm_mode = True
        allow_population_by_field_name = True

        json_encoders = {
            datetime: datetime_format
        }


class SystemItemImport(SystemItemType):

    @root_validator
    def check_size_type(cls, values):
        size = values.get('size')
        type = values.get('type')
        assert (ItemType(type) == ItemType.FOLDER and size is None) or (
                ItemType(type) == ItemType.FILE and size > 0)
        return values


class SystemItemImportRequest(BaseModel):
    items: List[SystemItemImport]
    update_date: datetime = Field(alias='updateDate')


class SystemItemHistoryUnit(SystemItemType):
    children: List['SystemItemHistoryUnit'] = None

    @validator('children')
    def replace_empty_list(cls, v):
        return v or None

    def get_child(self, index):
        if len(self.children) > index:
            return self.children[index]
        return None


class SystemItemHistoryResponse(BaseModel):
    items: List[SystemItemType]

    class Config:
        orm_mode = True


SystemItemHistoryUnit.update_forward_refs()