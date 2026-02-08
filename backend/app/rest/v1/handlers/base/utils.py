import re


def transform_class_name(original: str) -> str:
    base_name = original.removesuffix("Handler") if original.endswith("Handler") else original

    transformed = re.sub(r"(?<!^)(?=[A-Z])", "_", base_name)

    return transformed.lower()
