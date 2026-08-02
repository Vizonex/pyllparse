from dataclasses import dataclass, field


# NOTE: Got rid of the naming convention of IUniqueName
# for just UniqueName. It's not an interface in python
@dataclass(slots=True, unsafe_hash=True)
class UniqueName:
    name: str
    original_name: str


@dataclass(slots=True, frozen=True)
class Identifier:
    prefix: str = ""
    postfix: str = ""
    ns: set[str] = field(init=False, default_factory=set)

    def id(self, name: str):
        target = self.prefix + name + self.postfix

        if target in self.ns:
            for i in range(1, len(self.ns) + 1):
                new_target = f"{target}_{i}"
                if new_target not in self.ns:
                    target = new_target
                    break

        self.ns.add(target)
        return UniqueName(name=target, original_name=name)
