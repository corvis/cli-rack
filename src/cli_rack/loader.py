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
import inspect
import json
import logging
import os
import re
import shutil
import urllib.request
from abc import abstractmethod, ABCMeta
from typing import Optional, Union, Callable, List, Type, Tuple, Sequence
from zipfile import ZipFile

from cli_rack import utils
from cli_rack.exception import CLIRackError
from cli_rack.serialize import DateTimeEncoder, DateTimeDecoder


class LoaderError(CLIRackError):
    def __init__(
        self,
        msg,
        *args,
        fix_hint: Optional[str] = None,
        locator: Optional["BaseLocatorDef"] = None,
        meta: Optional["LoadedDataMeta"] = None,
    ) -> None:
        super().__init__(msg, *args, fix_hint=fix_hint)
        self.meta = meta
        self.__locator = locator

    @property
    def locator(self) -> Optional["BaseLocatorDef"]:
        if self.__locator is not None:
            return self.__locator
        elif self.meta is not None:
            return self.meta.locator
        else:
            return None


class InvalidPackageStructure(LoaderError):
    def __init__(self, meta: "LoadedDataMeta", details: Optional[str] = None, hint: Optional[str] = None) -> None:
        message = "Package {} has invalid " "structure (directory layout){}".format(
            meta.locator, ": " + details if details is not None else ""
        )
        super().__init__(message, meta=meta, fix_hint=hint)


class BaseLocatorDef(metaclass=ABCMeta):
    PATH_SEPARATOR = "/"
    PREFIX: str
    TYPE: str

    def __init__(self, name: str, original_locator: Optional[str] = None) -> None:
        self.name = name
        self.original_locator = original_locator

    @classmethod
    def generate_hash_suffix(cls, suffix: str) -> str:
        return hashlib.sha1(suffix.encode()).hexdigest()[:8]

    def to_dict(self) -> dict:
        return dict(type=self.TYPE, original_locator=self.original_locator)

    @classmethod
    @abstractmethod
    def from_dict(cls, locator_dict: dict):
        pass

    def __str__(self) -> str:
        return (
            self.original_locator
            if self.original_locator is not None
            else "Locator<{}> -> {}".format(self.TYPE, self.name)
        )

    def __copy__(self):
        return self.from_dict(self.to_dict())


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

    @classmethod
    def from_dict(cls, meta_dict: dict, path: str, registry: Optional["LoaderRegistry"] = None):
        locator_dict = utils.safe_cast(dict, meta_dict.get("locator"))
        if registry is None:
            registry = DefaultLoaderRegistry
        loader_cls = registry.get_for_locator_dict(locator_dict)
        if loader_cls is None:
            raise LoaderError("Unknown locator declared in package {}".format(path))
        locator = loader_cls.LOCATOR_CLS.from_dict(locator_dict)
        meta = LoadedDataMeta(locator, path, meta_dict["target_path"])
        meta.timestamp = meta_dict["timestamp"]
        meta.is_file = meta_dict["is_file"]
        return meta


class BaseLoader(object, metaclass=ABCMeta):
    LOCATOR_PREFIX_DELIMITER = ":"
    META_FILE_NAME = "meta.json"
    LOCATOR_CLS: Type[BaseLocatorDef]

    def __init__(self, logger: logging.Logger, target_dir="tmp/external") -> None:
        self.target_dir = target_dir
        self._logger = logger
        self.reload_interval: Optional[datetime.timedelta] = None

    @classmethod
    def _remove_locator_prefix(cls, data: str):
        return data.replace(cls.LOCATOR_CLS.PREFIX + cls.LOCATOR_PREFIX_DELIMITER, "", 1)

    @classmethod
    def can_handle(cls, locator: Union[str, BaseLocatorDef]) -> bool:
        if isinstance(locator, str):
            return locator.startswith(cls.LOCATOR_CLS.PREFIX + cls.LOCATOR_PREFIX_DELIMITER)
        elif isinstance(locator, BaseLocatorDef):
            return cls.LOCATOR_CLS == locator.__class__
        else:
            raise ValueError(
                "Locator must be either string or subclass of BaseLocatorDef, but {} given".format(
                    locator.__class__.__name__
                )
            )

    @classmethod
    def locator_to_locator_def(cls, locator_str: Union[str, BaseLocatorDef]) -> BaseLocatorDef:
        pass

    @abstractmethod
    def load(
        self,
        locator: Union[str, BaseLocatorDef],
        target_path_resolver: Optional[Callable[[LoadedDataMeta], str]] = None,
        force_reload=False,
    ) -> LoadedDataMeta:
        raise NotImplementedError

    def write_meta(self, meta: LoadedDataMeta):
        with open(os.path.join(meta.path, self.META_FILE_NAME), "w") as f:
            json.dump(meta.to_dict(), f, cls=DateTimeEncoder)

    def read_meta(self, package_path: str):
        try:
            with open(os.path.join(package_path, self.META_FILE_NAME), "r") as f:
                meta_dict = json.load(f, cls=DateTimeDecoder)
                return LoadedDataMeta.from_dict(meta_dict, package_path)
        except Exception as e:
            raise LoaderError("Package {} metadata is missing or corrupted".format(package_path)) from e

    def verify_existing_package(self, local_path: str) -> Optional[LoadedDataMeta]:
        if os.path.isdir(local_path):
            try:
                meta = self.read_meta(local_path)
            except LoaderError:
                self._logger.debug("Package exists, but it is corrupted. Removing.")
                shutil.rmtree(local_path)
                return None
            return meta  # Package exists and it is ok
        return None

    def is_reload_required(self, meta: Optional[LoadedDataMeta]) -> bool:
        if meta is None or meta.timestamp is None:
            return True
        if self.reload_interval is not None:
            return datetime.datetime.now() - meta.timestamp > self.reload_interval
        return False

    def _prepare_meta(
        self,
        locator: BaseLocatorDef,
        path: str,
        target_path_resolver: Optional[Callable[[LoadedDataMeta], str]] = None,
    ):
        meta = LoadedDataMeta(locator, path)
        if target_path_resolver is not None:
            meta.target_path = target_path_resolver(meta)
        else:
            meta.target_path = ""
        return meta

    def _check_if_should_load(self, path: str, force_reload: bool) -> Tuple[Optional[LoadedDataMeta], bool]:
        meta = self.verify_existing_package(path)
        if meta is not None:
            self._logger.info("Existing package found")
            if force_reload:
                self._logger.debug("Package exists. Reloading is forced")
                shutil.rmtree(path)
                return meta, True
            else:
                is_reload_required = self.is_reload_required(meta)
                if is_reload_required:
                    self._logger.info("Package is outdated and will be reloaded")
                    shutil.rmtree(path)
                return meta, self.is_reload_required(meta)
        return None, True

    def _write_meta(self, meta: LoadedDataMeta) -> LoadedDataMeta:
        self._logger.debug("Writing meta data for " + str(meta.locator))
        self.write_meta(meta)
        self._logger.info("Loaded " + str(meta.locator))
        return meta


class LoaderRegistry(object):
    def __init__(self) -> None:
        super().__init__()
        self.__registry: List[BaseLoader] = []
        self.__target_dir: Optional[str] = None

    @property
    def target_dir(self) -> Optional[str]:
        return self.__target_dir

    @target_dir.setter
    def target_dir(self, val: str):
        self.__target_dir = val
        for x in self.__registry:
            x.target_dir = self.__target_dir

    def __instantinate_loader(self, loader_cls: Type[BaseLoader]) -> BaseLoader:
        try:
            return loader_cls(target_dir=self.target_dir)  # type: ignore
        except Exception as e:
            raise LoaderError(
                "Unable to instantiate {}. "
                "Loader must declare constructor which expects the following "
                "kwargs: target_dir".format(loader_cls.__name__)
            ) from e

    def register(self, loader: Union[Type[BaseLoader], BaseLoader]) -> BaseLoader:
        if inspect.isclass(loader) and issubclass(loader, BaseLoader):  # type: ignore
            instance = self.__instantinate_loader(loader)  # type: ignore
            self.__registry.append(instance)
            return instance
        elif isinstance(loader, BaseLoader):
            self.__registry.append(loader)
            return loader
        else:
            raise ValueError("LoadRegistry expects subclass of BaseLoader but {} was given".format(loader.__name__))

    def register_all(self, loaders: Sequence[Union[Type[BaseLoader], BaseLoader]]):
        for x in loaders:
            self.register(x)

    def parse_locator(self, locator: Union[str, dict, BaseLocatorDef]) -> Optional[BaseLocatorDef]:
        if locator is None:
            return None
        if isinstance(locator, str) or isinstance(locator, BaseLocatorDef):
            loader = self.get_for_locator(locator)
        elif isinstance(locator, dict):
            loader = self.get_for_locator_dict(locator)
        else:
            raise LoaderError(
                "Locator must be any of str, dict or subclass of BaseLocatorDef but {} given".format(
                    locator.__class__.__name__
                )
            )
        if loader is None:
            raise LoaderError("Locator {} is not supported".format(str(locator)))
        if isinstance(locator, dict):
            return loader.LOCATOR_CLS.from_dict(locator)
        return loader.locator_to_locator_def(locator)

    def get_for_locator(self, locator: Union[str, BaseLocatorDef]) -> Optional[BaseLoader]:
        for x in self.__registry:
            if x.can_handle(locator):
                return x
        return None

    def get_for_locator_dict(self, locator_dict: dict) -> Optional[BaseLoader]:
        target_type = locator_dict.get("type")
        if target_type is None:
            return None
        for x in self.__registry:
            if x.LOCATOR_CLS.TYPE == target_type:
                return x
        return None

    def load(
        self,
        locator: Union[str, BaseLocatorDef],
        target_path_resolver: Optional[Callable[[LoadedDataMeta], str]] = None,
        force_reload=False,
    ) -> LoadedDataMeta:
        loader = self.get_for_locator(locator)
        if loader is None:
            raise LoaderError("Locator {} is not supported".format(str(locator)))
        return loader.load(locator, target_path_resolver=target_path_resolver, force_reload=force_reload)

    def clone(self) -> "LoaderRegistry":
        res = LoaderRegistry()
        res.register_all(self.__registry)
        res.target_dir = self.__target_dir
        return res


DefaultLoaderRegistry = LoaderRegistry()


# ================== Local File System Loader =================


class LocalLocatorDef(BaseLocatorDef):
    PREFIX = "local"
    TYPE = "local"

    def __init__(self, path: str, original_locator: Optional[str] = None) -> None:
        super().__init__(self.path_to_name(path), original_locator)
        self.path = path

    @classmethod
    def path_to_name(cls, path: str):
        return os.path.basename(path) + "-" + cls.generate_hash_suffix(path)

    def to_dict(self) -> dict:
        result = super().to_dict()
        result.update(dict(path=self.path))
        return result

    @classmethod
    def from_dict(cls, locator_dict: dict):
        return cls(locator_dict["path"], locator_dict.get("original_locator"))


@DefaultLoaderRegistry.register
class LocalLoader(BaseLoader):
    LOCATOR_CLS = LocalLocatorDef

    def __init__(self, target_dir="tmp/external") -> None:
        super().__init__(logging.getLogger("loader.local"), target_dir)

    @classmethod
    def locator_to_locator_def(cls, locator_str: Union[str, BaseLocatorDef]) -> LocalLocatorDef:
        if isinstance(locator_str, str):
            return cls.LOCATOR_CLS(
                path=cls._remove_locator_prefix(locator_str),
                original_locator=locator_str,
            )
        elif isinstance(locator_str, cls.LOCATOR_CLS):
            return locator_str
        else:
            raise ValueError(
                "Locator should be either locator string or LocalLocatorDef got {}".format(
                    locator_str.__class__.__name__
                )
            )

    @classmethod
    def resolve_path(cls, path: str) -> str:
        if not os.path.exists(path):
            raise CLIRackError('Invalid locator: path "{}" doesn\'t exist'.format(path))
        return path

    def load(
        self,
        locator_: Union[str, BaseLocatorDef],
        target_path_resolver: Optional[Callable[[LoadedDataMeta], str]] = None,
        force_reload=False,
    ) -> LoadedDataMeta:
        self._logger.info("Loading " + str(locator_))
        locator = self.locator_to_locator_def(locator_)
        fs_target = os.path.join(self.target_dir, locator.name)
        fs_source = self.resolve_path(locator.path)
        meta, is_reload_required = self._check_if_should_load(fs_target, force_reload)
        if not is_reload_required:
            self._logger.info("Cached version is up do date")
            return utils.none_throws(meta)
        # create empty target dir
        utils.ensure_dir(fs_target)
        self._logger.debug("\tTarget path: " + fs_target)
        self._logger.debug("\tSource path: " + fs_source)
        if os.path.isfile(fs_source):
            file_name = os.path.basename(fs_source)
            shutil.copy(fs_source, fs_target)
            meta = LoadedDataMeta(locator, fs_target, file_name)
            meta.is_file = True
        elif os.path.isdir(fs_source):
            shutil.copytree(fs_source, fs_target, dirs_exist_ok=True)  # type: ignore
            meta = LoadedDataMeta(locator, fs_target)
            meta.is_file = False
            if target_path_resolver is not None:
                meta.target_path = target_path_resolver(meta)
            else:
                meta.target_path = ""
        else:
            raise CLIRackError(
                "Locator {} points invalid location. It must be either file or directory".format(locator_)
            )
        return self._write_meta(meta)


DefaultLoaderRegistry.register(LocalLoader)


# ================== GIT Loader =================


class GitLocatorDef(BaseLocatorDef):
    TYPE = "git"
    PREFIX = "git"

    def __init__(
        self, url: str, ref: Optional[str] = None, name: Optional[str] = None, original_locator: Optional[str] = None
    ) -> None:
        self.url = url
        self.ref = ref
        name = name or self.__generate_name()
        super().__init__(name, original_locator)

    def to_dict(self) -> dict:
        result = super().to_dict()
        result.update(dict(url=self.url, ref=self.ref))
        return result

    def __generate_name(self):
        return "-".join((self.generate_hash_suffix(self.url + ("@" + self.ref if self.ref else "")),))

    @classmethod
    def from_dict(cls, locator_dict: dict):
        return cls(locator_dict["url"], locator_dict["ref"], locator_dict.get("original_locator"))


class GithubLocatorDef(GitLocatorDef):
    PREFIX = "github"
    TYPE = "github"

    def __init__(
        self, user_name: str, repo_name: str, ref: Optional[str] = None, original_locator: Optional[str] = None
    ) -> None:
        url = "https://github.com/{}/{}.git".format(user_name, repo_name)
        self.user_name = user_name
        self.repo_name = repo_name
        self.url = url
        self.ref = url
        super().__init__(url, ref, self.__generate_name(), original_locator)

    def __generate_name(self):
        return "-".join(
            (self.user_name, self.repo_name, self.generate_hash_suffix(self.url + ("@" + self.ref if self.ref else "")))
        )

    def to_dict(self) -> dict:
        result = super().to_dict()
        result.update(dict(user_name=self.user_name, repo_name=self.repo_name, ref=self.ref))
        return result

    @classmethod
    def from_dict(cls, locator_dict: dict):
        return cls(
            locator_dict["user_name"],
            locator_dict["repo_name"],
            locator_dict.get("ref"),
            locator_dict.get("original_locator"),
        )


class GithubLoader(BaseLoader):
    LOCATOR_CLS = GithubLocatorDef
    LOCATOR_RE = re.compile(
        LOCATOR_CLS.PREFIX
        + BaseLoader.LOCATOR_PREFIX_DELIMITER
        + r"//?([a-zA-Z0-9\-]+)/([a-zA-Z0-9\-\._]+)(?:@([a-zA-Z0-9\-_.\./]+))?"
    )
    GITHUB_ZIP_URL = "https://api.github.com/repos/{user}/{repo}/zipball/{ref}"
    LOCAL_ZIPBALL_NAME = "zipball.zip"

    def __init__(self, target_dir="tmp/external") -> None:
        super().__init__(logging.getLogger("loader.github"), target_dir)
        self.reload_interval = datetime.timedelta(days=1)

    @classmethod
    def locator_to_locator_def(cls, locator_str: Union[str, BaseLocatorDef]) -> GithubLocatorDef:
        if isinstance(locator_str, str):
            match = cls.LOCATOR_RE.match(locator_str)
            if match is None:
                raise LoaderError(
                    'Invalid github locator "{}". '
                    "Supported format is {}".format(
                        locator_str,
                        cls.LOCATOR_CLS.PREFIX + BaseLoader.LOCATOR_PREFIX_DELIMITER + "username/name[@branch-or-tag]",
                    )
                )
            return GithubLocatorDef(
                user_name=match.group(1),
                repo_name=match.group(2),
                ref=match.group(3),
                original_locator=locator_str,
            )
        elif isinstance(locator_str, GithubLocatorDef):
            return locator_str
        else:
            raise ValueError(
                "Locator should be either locator string or GithubLocatorDef got {}".format(
                    locator_str.__class__.__name__
                )
            )

    def load(
        self,
        locator_: Union[str, BaseLocatorDef],
        target_path_resolver: Optional[Callable[[LoadedDataMeta], str]] = None,
        force_reload=False,
    ) -> LoadedDataMeta:
        self._logger.info("Loading " + str(locator_))
        locator = self.locator_to_locator_def(locator_)
        fs_target = os.path.join(self.target_dir, locator.name)
        source_url = self.GITHUB_ZIP_URL.format(user=locator.user_name, repo=locator.repo_name, ref=locator.ref or "")
        # if target dir already exists - remove it
        meta, is_reload_required = self._check_if_should_load(fs_target, force_reload)
        if not is_reload_required:
            self._logger.info("Local copy exists and it is up to date")
            return utils.none_throws(meta)
        utils.ensure_dir(fs_target)
        self._logger.debug("\tTarget path: " + fs_target)
        self._logger.debug("\tSource path: " + source_url)
        zipball_path = os.path.join(fs_target, self.LOCAL_ZIPBALL_NAME)
        try:
            self._logger.info("\tDownloading archive from github: " + source_url)
            urllib.request.urlretrieve(source_url, zipball_path)
        except IOError as e:
            raise LoaderError("Unable to fetch remote resource {}:{}".format(str(locator_), str(e))) from e
        try:
            with ZipFile(zipball_path, "r") as z:
                dir_name = z.namelist()[0]
                z.extractall(fs_target)
            # Move all files from dir_name one level up
            dir_path = os.path.join(fs_target, dir_name)
            for file_name in os.listdir(dir_path):
                shutil.move(os.path.join(dir_path, file_name), fs_target)
            os.rmdir(dir_path)
        except Exception as e:
            raise LoaderError("Unable to unpack the resource {}:{}".format(str(locator_), str(e))) from e
        os.remove(zipball_path)
        meta = self._prepare_meta(locator, fs_target, target_path_resolver)
        return self._write_meta(meta)

    def _prepare_meta(
        self, locator: BaseLocatorDef, path: str, target_path_resolver: Optional[Callable[[LoadedDataMeta], str]] = None
    ) -> LoadedDataMeta:
        meta = super()._prepare_meta(locator, path, target_path_resolver)
        meta.is_file = False
        return meta


DefaultLoaderRegistry.register(GithubLoader)
