"""Stable errors at the CLI boundary."""


class DasyncError(Exception):
    def __init__(self, code: str, message: str, hint: str | None = None):
        super().__init__(message)
        self.code, self.hint = code, hint

    def as_dict(self) -> dict:
        return {"code": self.code, "message": str(self), "hint": self.hint}
