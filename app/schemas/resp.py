from typing import Generic, TypeVar

from pydantic.generics import GenericModel

DataT = TypeVar('DataT')  # 定义泛型


class RESPModel(GenericModel, Generic[DataT]):
    code: int
    message: str
    result: DataT
