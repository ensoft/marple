import uuid


def create_name():
    """Create a new unique generic name for a file"""
    name = str(uuid.uuid4())
    return name
