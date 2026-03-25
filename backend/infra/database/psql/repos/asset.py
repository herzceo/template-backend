from typing import final

from backend.domain.entities.asset import Asset
from backend.domain.repos.asset import AssetRepo

from .base import ImplCRUDSupported


@final
class ImplAssetRepo(ImplCRUDSupported[Asset], AssetRepo):
    __slots__ = ()
