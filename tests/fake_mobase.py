# Made by Claude Ai & Relic Hunter
import sys
import types
from enum import Enum, IntFlag


class FileTypes(IntFlag):
    FILE = 1
    DIRECTORY = 2
    FILE_OR_DIRECTORY = 3


class InsertPolicy(Enum):
    FAIL_IF_EXISTS = 0
    REPLACE = 1
    MERGE = 2


class FileTreeEntry:
    FileTypes = FileTypes

    def __init__(self, name, parent=None):
        self._name = name
        self._parent = parent

    def name(self):
        return self._name

    def parent(self):
        return self._parent

    def detach(self):
        if self._parent is not None:
            self._parent._children = [c for c in self._parent._children if c is not self]
            self._parent = None
        return True

    def path(self, sep="\\"):
        parts = []
        node = self
        while node is not None and node._parent is not None:
            parts.append(node._name)
            node = node._parent
        return sep.join(reversed(parts))


class IFileTree(FileTreeEntry):
    InsertPolicy = InsertPolicy

    def __init__(self, name="", parent=None):
        super().__init__(name, parent)
        self._children = []

    def __iter__(self):
        return iter(list(self._children))

    def __len__(self):
        return len(self._children)

    def __bool__(self):
        return len(self._children) > 0

    def _child(self, name):
        for c in self._children:
            if c._name.casefold() == name.casefold():
                return c
        return None

    def find(self, path, type=FileTypes.FILE_OR_DIRECTORY):
        node = self
        for part in [p for p in path.replace("\\", "/").split("/") if p]:
            if not isinstance(node, IFileTree):
                return None
            node = node._child(part)
            if node is None:
                return None
        if node is self:
            return None
        want_dir = isinstance(node, IFileTree)
        if type == FileTypes.DIRECTORY and not want_dir:
            return None
        if type == FileTypes.FILE and want_dir:
            return None
        return node

    def exists(self, path, type=FileTypes.FILE_OR_DIRECTORY):
        return self.find(path, type) is not None

    def addDirectory(self, path):
        node = self
        for part in [p for p in path.replace("\\", "/").split("/") if p]:
            child = node._child(part)
            if child is None:
                child = IFileTree(part, node)
                node._children.append(child)
            node = child
        return node

    def addFile(self, path):
        parts = [p for p in path.replace("\\", "/").split("/") if p]
        parent = self.addDirectory("/".join(parts[:-1])) if len(parts) > 1 else self
        f = FileTreeEntry(parts[-1], parent)
        parent._children.append(f)
        return f

    def _insert(self, entry, name, policy):
        existing = self._child(name)
        if existing is not None and existing is not entry:
            if policy == InsertPolicy.MERGE and isinstance(existing, IFileTree) and isinstance(entry, IFileTree):
                for c in list(entry._children):
                    existing._insert(c, c._name, policy)
                entry.detach()
                return True
            if policy == InsertPolicy.FAIL_IF_EXISTS:
                return False
            existing.detach()
        entry.detach()
        entry._name = name
        entry._parent = self
        self._children.append(entry)
        return True

    def move(self, entry, path, policy=InsertPolicy.FAIL_IF_EXISTS):
        path = path.replace("\\", "/")
        if path == "":
            return self._insert(entry, entry._name, policy)
        if path.endswith("/"):
            return self.addDirectory(path)._insert(entry, entry._name, policy)
        parts = path.split("/")
        target = self.addDirectory("/".join(parts[:-1])) if len(parts) > 1 else self
        return target._insert(entry, parts[-1], policy)

    def files(self, prefix=""):
        out = []
        for c in self._children:
            p = prefix + c._name
            if isinstance(c, IFileTree):
                out += c.files(p + "/") or [p + "/"]
            else:
                out.append(p)
        return out


class ModDataChecker:
    INVALID = "INVALID"
    FIXABLE = "FIXABLE"
    VALID = "VALID"
    CheckReturn = str

    def __init__(self):
        pass


class ModDataContent:
    class Content:
        def __init__(self, id, name, icon, filter_only=False):
            self.id, self.name, self.icon = id, name, icon

    def __init__(self):
        pass


class _Plugin:
    def __init__(self, *a, **k):
        pass


def install():
    m = types.ModuleType("mobase")
    m.FileTreeEntry = FileTreeEntry
    m.IFileTree = IFileTree
    m.ModDataChecker = ModDataChecker
    m.ModDataContent = ModDataContent
    for name in ("IPluginFileMapper", "IPluginDiagnose", "IPluginGame", "IOrganizer", "IModInterface",
                 "Mapping", "PluginSetting", "ExecutableInfo", "ExecutableForcedLoadSetting", "GameFeature"):
        setattr(m, name, type(name, (_Plugin,), {}))
    m.ModState = IntFlag("ModState", "EXISTS ACTIVE ESSENTIAL EMPTY ENDORSED VALID ALTERNATE")
    sys.modules["mobase"] = m
    return m


def tree_from(paths):
    root = IFileTree()
    for p in paths:
        p = p.replace("\\", "/")
        if p.endswith("/"):
            root.addDirectory(p)
        else:
            root.addFile(p)
    return root
