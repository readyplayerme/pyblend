# <pep8 compliant>


class DummyOperator:
    """Dummy to provide the report method used by export operations."""

    def __init__(self):
        self.messages = []

    def report(self, type, message):
        """Catch messages instead of reporting them."""
        self.messages.append((type.pop(), message))
