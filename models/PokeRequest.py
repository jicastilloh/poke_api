from pydantic import BaseModel, Field
from typing import Optional


class PokemonRequest(BaseModel):
    id: Optional[int] = Field(
        default=None,
        ge=1,
        description="ID de la petición"
    )

    pokemon_type: Optional[str] = Field(
        default=None,
        description="Tipo de pokemon",
        pattern="^[a-zA-Z0-9_]+$"
    )

    url: Optional[str] = Field(
        default=None,
        description="Url de la petición",
        pattern="^https?://[^\s]+$"
    )

    status: Optional[str] = Field(
        default=None,
        description="Estado de la pteición",
        pattern="^(sent|completed|failed|inprogress)"
    )
