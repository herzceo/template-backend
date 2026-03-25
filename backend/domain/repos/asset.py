from typing import Protocol

from backend.domain.entities.asset import Asset
from backend.domain.repos.base import CRUDSupported


class AssetRepo(CRUDSupported[Asset], Protocol): ...
