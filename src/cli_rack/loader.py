#    CLI Rack - Lightweight set of tools for building pretty-looking CLI applications in Python
#    Copyright (C) 2021 Dmitry Berezovsky
#    The MIT License (MIT)
#
#    Permission is hereby granted, free of charge, to any person obtaining
#    a copy of this software and associated documentation files
#    (the "Software"), to deal in the Software without restriction,
#    including without limitation the rights to use, copy, modify, merge,
#    publish, distribute, sublicense, and/or sell copies of the Software,
#    and to permit persons to whom the Software is furnished to do so,
#    subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be
#    included in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
#    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import datetime
import hashlib
import json
import os
import shutil
from abc import abstractmethod, ABCMeta
from typing import Optional, Union, Callable

from cli_rack import utils
from cli_rack.exception import CLIRackError
from cli_rack.serialize import DateTimeEncoder


class LoaderError(CLIRackError):

    def __init__(self, msg, *args, fix_hint: Optional[str] = None, locator: Optional['BaseLocatorDef'] = None,
                 meta: Optional['LoadedDataMeta'] = None) -> None:
        super().__init__(msg, *args, fix_hint=fix_hint)
        self.meta = meta
        self.__locator = locator

    @property
    def locator(self) -> Optional['BaseLocatorDef']:
        if self.__locator is not None:
            return self.__locator
        elif self.meta.locator is not None:
            return self.meta.locator
        else:
            return None


class InvalidPackageStructure(LoaderError):

    def __init__(self, meta: 'LoadedDataMeta', details: Optional[str] = None, hint: Optional[str] = None) -> None:
        message = 'Package {} has invalid ' \
                  'structure (directory layout){}'.format(meta.locator, ': ' + details if details is not None else '')
        super().__init__(message, meta=meta, fix_hint=hint)


class BaseLocatorDef(metaclass=ABCMeta):
    PATH_SEPARATOR = "/"

    def __init__(self, type: str, name: str) -> None:
        self.type = type
        self.name = name
        self.original_locator: Optional[str] = None

    @classmethod
    def generate_hash_suffix(cls, suffix: str) -> str:
        return hashlib.sha1(suffix.encode()).hexdigest()[:8]

    def to_dict(self) -> dict:
        return dict(type=self.type)


class LoadedDataMeta(object):
    def __init__(self, locator: BaseLocatorDef, path: str, target_path: Optional[str] = None) -> None:
        self.locator = locator
        self.path = path
        self.target_path = target_path
        self.is_file: Optional[bool] = None
        self.timestamp: Optional[datetime.datetime] = datetime.datetime.now()

    def to_dict(self):
        return dict(
            timestamp=self.timestamp,
            locator=self.locator.to_dict() if self.locator else None,
            target_path=self.target_path,
            is_file=self.is_file,
        )


class BaseLoader(object, metaclass=ABCMeta):
    LOCATOR_PREFIX_DELIMITER = ":"
    META_FILE_NAME = "meta.json"
    LOCATOR_PREFIX: str

    def __init__(self, target_dir="tmp/external") -> None:
        self.target_dir = target_dir

    def can_handle(self, locator: str) -> bool:
        return locator.startswith(self.LOCATOR_PREFIX + self.LOCATOR_PREFIX_DELIMITER)

    def locator_to_locator_def(self, locator_str: str) -> BaseLocatorDef:
        pass

    @abstractmethod
    def load(self, locator: Union[str, BaseLocatorDef],
             target_path_resolver: Optional[Callable[[LoadedDataMeta], str]] = None) -> LoadedDataMeta:
        raise NotImplementedError

    def write_meta(self, meta: LoadedDataMeta):
        with open(os.path.join(meta.path, self.META_FILE_NAME), "w") as f:
            json.dump(meta.to_dict(), f, cls=DateTimeEncoder)


# ================== Local File System Loader =================

class LocalLocatorDef(BaseLocatorDef):
    def __init__(self, type: str, path: str) -> None:
        super().__init__(type, self.path_to_name(path))
        self.path = path

    @classmethod
    def path_to_name(cls, path: str):
        return os.path.basename(path) + "-" + cls.generate_hash_suffix(path)

    def to_dict(self) -> dict:
        return dict(type=self.type, path=self.path)

    def __str__(self) -> str:
        return "".join((self.type, BaseLoader.LOCATOR_PREFIX_DELIMITER, self.path))


class LocalLoader(BaseLoader):
    LOCATOR_PREFIX = "local"

    def locator_to_locator_def(self, locator_str: Union[str, BaseLocatorDef]) -> LocalLocatorDef:
        if isinstance(locator_str, str):
            return LocalLocatorDef(
                type="local", path=locator_str.replace(self.LOCATOR_PREFIX + self.LOCATOR_PREFIX_DELIMITER, "", 1)
            )
        elif isinstance(locator_str, LocalLocatorDef):
            return locator_str
        else:
            raise ValueError(
                "Locator should be either locator string or LocatorDef got {}".format(
                    locator_str.__class__.__name__)
            )

    @classmethod
    def resolve_path(cls, path: str) -> str:
        if not os.path.exists(path):
            raise CLIRackError('Invalid locator: path "{}" doesn\'t exist'.format(path))
        return path

    def load(self, locator_: Union[str, BaseLocatorDef],
             target_path_resolver: Optional[Callable[[LoadedDataMeta], str]] = None) -> LoadedDataMeta:
        locator = self.locator_to_locator_def(locator_)
        fs_target = os.path.join(self.target_dir, locator.name)
        fs_source = self.resolve_path(locator.path)
        # if target dir already exists - remove it
        if os.path.isdir(fs_target):
            shutil.rmtree(fs_target)
        # create empty target dir
        utils.ensure_dir(fs_target)
        if os.path.isfile(fs_source):
            file_name = os.path.basename(fs_source)
            shutil.copy(fs_source, fs_target)
            meta = LoadedDataMeta(locator, fs_target, file_name)
            meta.is_file = True
        elif os.path.isdir(fs_source):
            shutil.copytree(fs_source, fs_target, dirs_exist_ok=True)
            meta = LoadedDataMeta(locator, fs_target)
            meta.is_file = False
            if target_path_resolver is not None:
                meta.target_path = target_path_resolver(meta)
            else:
                meta.target_path = ''
        else:
            raise CLIRackError(
                "Locator {} points invalid location. It must be either file or directory".format(locator_)
            )
        self.write_meta(meta)
        return meta
