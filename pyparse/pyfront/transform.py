from typing import Optional , Union 



# Transform {
#   constructor(public readonly name: string)

class Transform:
    def __init__(self,name:str) -> None:
        self.name = name

class ID(Transform):
    def __init__(self) -> None:
        super().__init__("id")

class ToLowerUnsafe(Transform):
    def __init__(self) -> None:
        super().__init__("to_lower_unsafe")

class ToLower(Transform):
    def __init__(self) -> None:
        super().__init__("to_lower")