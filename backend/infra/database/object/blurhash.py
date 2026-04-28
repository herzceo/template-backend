from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image
from fast_blurhash import encode

if TYPE_CHECKING:
    from PIL.ImageFile import ImageFile

_X_COMPONENTS = 4
_Y_COMPONENTS = 3
_THUMBNAIL_SIZE = (64, 64)
_IMAGE_CONTENT_TYPES = ("image/jpeg", "image/png", "image/gif", "image/webp")


def is_image(content_type: str) -> bool:
    return content_type in _IMAGE_CONTENT_TYPES


def compute(data: bytes) -> str:
    image: ImageFile = Image.open(BytesIO(data))
    image.thumbnail(_THUMBNAIL_SIZE)
    return encode(image, _X_COMPONENTS, _Y_COMPONENTS)
