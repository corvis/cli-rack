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

import argparse
import importlib
import inspect
import logging
import pkgutil
from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop
from typing import Optional, Sequence, List, Union, Iterable, NamedTuple, Type

from cli_rack import CLI
from cli_rack.exception import ExtensionUnavailableError, ExecutionManagerError
from cli_rack.utils import scalar_to_list


class CliExtension(ABC):
    """
    Allows to extend CLI interface
    """

    COMMAND_NAME: Optional[str] = None
    COMMAND_DESCRIPTION: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__()

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        pass

    def setup(self, *args, **kwargs):
        pass

    @abstractmethod
    def handle(self, args):
        raise NotImplementedError()

    def __repr__(self) -> str:
        return "<{}>".format(self.__class__.__qualname__)


class AsyncCliExtension(CliExtension):
    def __init__(self, loop: AbstractEventLoop, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__loop = loop

    @property
    def loop(self):
        return self.__loop

    async def handle(self, args):
        raise NotImplementedError()


class GlobalArgsExtension(ABC):
    def __init__(self, app_manager: Optional["CliAppManager"] = None) -> None:
        super().__init__()
        self.app_manager: Optional["CliAppManager"] = app_manager

    @classmethod
    def setup_parser(cls, parser: argparse.ArgumentParser):
        pass

    def handle(self, args):
        pass


class Availability(NamedTuple):
    is_available: bool
    unavailable_reason: Optional[str]
    recommendation: Optional[str]


class DiscoveredCliExtension(object):
    def __init__(self, package_name: str, availability: Optional[Availability]) -> None:
        self.package_name: str = package_name
        self.availability = availability
        self.module_name: Optional[str] = None
        self.cli_extension: Optional[Type[CliExtension]] = None

    @property
    def is_available(self):
        return self.availability.is_available

    @property
    def module_full_name(self) -> Optional[str]:
        return "{}.{}".format(self.package_name, self.module_name) if self.module_name is not None else None

    @property
    def full_name(self) -> Optional[str]:
        if None in (self.module_full_name, self.cli_extension):
            if self.package_name is not None:
                return self.package_name
            return None
        return ".".join((self.module_full_name, self.cli_extension.__name__))  # type: ignore

    def __repr__(self):
        module_name = self.module_full_name
        return "CliExtension<{}, {}>".format(
            self.package_name if module_name is None else module_name,
            self.cli_extension.__name__ if self.cli_extension else "n/a",
        )


class BaseExecutionManager(ABC):
    @classmethod
    def _instantiate_extension(cls, clazz: Type[CliExtension]) -> CliExtension:
        return clazz()

    @classmethod
    def _setup_extension(cls, ext: CliExtension):
        ext.setup()


class ExecutionManager(BaseExecutionManager):
    def __init__(self) -> None:
        super().__init__()
        self.__logger = logging.getLogger("cli.exec-mng")

    def run(self, commands: Sequence[argparse.Namespace]):
        try:
            for cmd in commands:
                self.__logger.debug("Running {}".format(cmd.cmd))
                try:
                    ext = self._instantiate_extension(cmd.ext_cls)
                    self._setup_extension(ext)
                except Exception as e:
                    raise ExecutionManagerError(
                        "Unable to instantiate extension for command {}: {}".format(cmd.cmd, str(e))
                    ) from e
                try:
                    ext.handle(cmd)
                except Exception as e:
                    msg = "Error during {} command execution: ".format(cmd.cmd) if len(commands) > 1 else ""
                    raise ExecutionManagerError(msg + str(e)) from e
        except ExecutionManagerError as e:
            CLI.print_error(e)


class AsyncExecutionManager(BaseExecutionManager):
    def __init__(self) -> None:
        super().__init__()
        self.__logger = logging.getLogger("cli.async-exec-mng")


class CliAppManager:
    def __init__(
        self,
        prog_name: str,
        add_commands_parser=True,
        allow_multiple_commands=True,
        description: str = None,
        epilog: str = None,
        **kwargs,
    ) -> None:
        super().__init__()
        self.__logger = logging.getLogger("cli.app-mng")
        self.discovery_manager = DiscoveryManager()
        self.available_extensions: List[Type[CliExtension]] = []
        self.global_args_extensions: List[Type[GlobalArgsExtension]] = []
        self.global_args_parser = argparse.ArgumentParser(add_help=False)
        self.args_parser = argparse.ArgumentParser(
            prog=prog_name,
            add_help=True,
            description=description,
            epilog=epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            **kwargs,
        )
        self.add_commands_parser = True
        self.allow_multiple_commands = False
        self.add_verbosity_control = True
        self.add_debug_mode_control = True
        self.add_discovered_unavailable_report = True
        self.show_unavailable_modules = False
        self.global_args: Optional[argparse.Namespace] = None
        self.setup_global()

    def register_extension(self, *ext_type: Type[CliExtension]) -> None:
        for x in ext_type:
            self.available_extensions.append(x)

    def register_global_args_extension(self, *ext_type: Type[GlobalArgsExtension]):
        for x in ext_type:
            self.global_args_extensions.append(x)

    def __read_global_args(self, args) -> argparse.Namespace:
        known, unknown = self.global_args_parser.parse_known_args(args)
        return known

    def __read_args(self, args) -> argparse.Namespace:
        known, unknown = self.args_parser.parse_known_args(args)
        return known

    def __setup_parser_for_global_args(self, parser: argparse.ArgumentParser):
        for ext_cls in self.global_args_extensions:
            ext_cls.setup_parser(parser)

    @classmethod
    def __configure_subparser_for_cli_extension(cls, ext_cls: Type[CliExtension], parser: argparse.ArgumentParser):
        ext_cls.setup_parser(parser)
        parser.set_defaults(ext_cls=ext_cls)

    def setup_global(self):
        # Configure global parser
        if self.add_debug_mode_control:
            from .cli_extension import DebugModeCliExtension

            self.register_global_args_extension(DebugModeCliExtension)
        if self.add_verbosity_control:
            from .cli_extension import VerboseModeCliExtension

            self.register_global_args_extension(VerboseModeCliExtension)
        if self.add_discovered_unavailable_report:
            from .cli_extension import ShowUnavailableModulesCliExtension

            self.register_global_args_extension(ShowUnavailableModulesCliExtension)
        self.__setup_parser_for_global_args(self.global_args_parser)

    def parse_global(self, args=None) -> argparse.Namespace:
        res = self.__read_global_args(args)
        self.global_args = res
        return res

    def parse_and_handle_global(self, args=None):
        parsed = self.parse_global(args)
        for ext in self.global_args_extensions:
            instance = ext(self)
            instance.handle(parsed)

    def setup(self):
        self.__setup_parser_for_global_args(self.args_parser)
        if self.add_commands_parser:
            command_parser = self.args_parser.add_subparsers(
                title="Available Commands",
                metavar="command",
                dest="cmd",
                description='Use "<command> -h" to get information ' "about particular command",
            )
            for ext_cls in self.available_extensions:
                ext_subparser = command_parser.add_parser(ext_cls.COMMAND_NAME, help=ext_cls.COMMAND_DESCRIPTION)
                self.__configure_subparser_for_cli_extension(ext_cls, ext_subparser)
            # if self.allow_multiple_commands:
            #     self.args_parser.add_argument(metavar='command', dest='extra', nargs="*", help='One or more commands')

    def __report_unrecognized_args(self, unknown: Sequence[str]):
        msg = "unrecognized arguments: %s"
        self.args_parser.error(msg % " ".join(unknown))

    def parse(self, args):
        command_args, unknown = self.args_parser.parse_known_args(args)
        commands = [command_args]
        if self.allow_multiple_commands:
            prev = unknown.copy()
            while unknown:
                command_args, unknown = self.args_parser.parse_known_args(unknown)
                # If after second run the unknown args are the same then they must be really unknown
                # and we don't have any consumer
                if prev == unknown:
                    self.__report_unrecognized_args(unknown)
                    break
                else:
                    prev = unknown
                commands.append(command_args)
        elif len(unknown) > 0:
            self.__report_unrecognized_args(unknown)
        return commands

    def discover_and_register_extensions(
        self,
        package_to_scan: Union[str, Iterable[str]],
        scan_module: Union[str, Iterable[str]] = "cli",
        report_unavailable: Optional[bool] = None,
    ) -> Sequence[DiscoveredCliExtension]:
        discovered = self.discovery_manager.discover_cli_extensions(package_to_scan, scan_module, False)
        show_unavailable = report_unavailable if report_unavailable is not None else self.show_unavailable_modules
        for x in discovered:
            if x.is_available:
                if x.cli_extension is None:
                    self.__logger.warning(
                        "Ignored extension {}. It is marked as available but class is not assigned. "
                        "This might be caused by internal data inconsistency due to some bug.".format(x.full_name)
                    )
                    continue
                self.register_extension(x.cli_extension)
            elif show_unavailable:
                self.report_unavailable_extension(x)
        return discovered

    @classmethod
    def report_unavailable_extension(cls, ext: DiscoveredCliExtension):
        CLI.print_warn("WARNING: Module {} is unavailable".format(ext.full_name))
        if ext.availability:
            if ext.availability.unavailable_reason:
                CLI.print_warn("\t\t Reason: {}".format(ext.availability.unavailable_reason))
            if ext.availability.recommendation:
                CLI.print_warn("\t\t Tip: {}".format(ext.availability.recommendation))

    @classmethod
    def create_execution_manager(cls) -> ExecutionManager:
        return ExecutionManager()

    @classmethod
    def create_async_execution_manager(cls) -> AsyncExecutionManager:
        return AsyncExecutionManager()


class DiscoveryManager:
    def __init__(self) -> None:
        super().__init__()
        self.__logger = logging.getLogger("cli.discovery")

    def is_package_available(self, pkg_obj: object) -> Availability:
        if hasattr(pkg_obj, "is_available"):
            try:
                if not pkg_obj.is_available():  # type: ignore
                    return Availability(False, None, None)
            except ExtensionUnavailableError as e:
                return Availability(False, str(e), e.fix_hint)
            except:  # noqa: E722
                self.__logger.warning(
                    "CLI discovery probe caught exception during package availability check for {}:\n"
                    "This might indicate incorrect implementation of the is_available method which "
                    "should either return boolean or raise ExtensionUnavailableError error",
                    exc_info=True,
                )
                return Availability(False, None, None)

        return Availability(True, None, None)

    def discover_cli_extensions(
        self,
        package_to_scan: Union[str, Iterable[str]],
        scan_module: Union[str, Iterable[str]] = "cli",
        ignore_unavailable=True,
    ) -> Sequence[DiscoveredCliExtension]:
        """

        :param package_to_scan: string or string[], full name of the package to scan for extensions
        :param scan_module: string or string[], name of the module within the package to scan for extension classes
        :return:
        """
        extensions: List[DiscoveredCliExtension] = []
        for package_name in scalar_to_list(package_to_scan):  # type: str
            try:
                self.__logger.debug("Scanning package {}".format(package_name))
                target_package = importlib.import_module(package_name)
                for loader, pkg_name, is_pkg in pkgutil.walk_packages(target_package.__path__):  # type: ignore
                    # Check if we've got a valid extension package
                    if is_pkg:
                        full_name = ".".join((target_package.__name__, pkg_name))
                        candidate_pkg = importlib.import_module(full_name)
                        availability = self.is_package_available(candidate_pkg)
                        discovered_extension = DiscoveredCliExtension(full_name, availability)
                        if not availability.is_available:
                            if not ignore_unavailable:
                                extensions.append(discovered_extension)
                            continue
                        # Scanning modules
                        try:
                            for module_name in scalar_to_list(scan_module):
                                cli_module = importlib.import_module("." + module_name, full_name)
                                found_extensions = inspect.getmembers(
                                    cli_module,
                                    lambda member: inspect.isclass(member)
                                    and member != CliExtension
                                    and issubclass(member, CliExtension),
                                )
                                for e_name, e in found_extensions:
                                    ext = DiscoveredCliExtension(
                                        discovered_extension.package_name, discovered_extension.availability
                                    )
                                    ext.module_name = module_name
                                    ext.cli_extension = e  # type: ignore
                                    self.__logger.debug("\tDiscovered CLI extension: {}".format(ext.full_name))
                                    extensions.append(ext)
                        except ImportError:
                            pass
            except ImportError:
                self.__logger.warning("Package {} doesn't exist".format(package_name))
        self.__logger.debug(
            "Discovered {} extension(-s)".format(len(list(filter(lambda x: x.is_available, extensions))))
        )
        return extensions
