from dataclasses import dataclass


class QuartDishkaError(Exception):
    """Base class for all QuartDishka exceptions"""


@dataclass(eq=False)
class ContainerNotSetError(QuartDishkaError):
    """Exception raised when the container is not set"""

    message: str = "Container must be set before initializing app"

    def __init__(self) -> None:
        super().__init__(self.message)

    @property
    def title(self) -> str:
        return self.message
