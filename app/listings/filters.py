from dataclasses import dataclass
from typing import Optional

from app.listings.models import DealType, PropertyType


@dataclass
class ListingFilters:
    """Общие query-параметры фильтрации объявлений.

    Используется как Depends() в GET /listings и GET /listings/map —
    гарантирует идентичный набор фильтров на обоих эндпоинтах.
    Добавить новый фильтр нужно только здесь.
    """

    city: Optional[str] = None
    deal_type: Optional[DealType] = None
    property_type: Optional[PropertyType] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    rooms: Optional[int] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    floor_min: Optional[int] = None
    floor_max: Optional[int] = None
