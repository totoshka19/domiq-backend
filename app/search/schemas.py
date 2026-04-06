from pydantic import BaseModel


class AutocompleteItem(BaseModel):
    city: str
    count: int


class AutocompleteResponse(BaseModel):
    items: list[AutocompleteItem]
