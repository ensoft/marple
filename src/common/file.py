import uuid


def create_name():
    """Create a new unique generic name for a file"""
    # TODO: Add differet kinds of naming
    name = str(uuid.uuid4())
    return name
