import os

from cli_rack import CLI, ansi
from cli_rack.loader import LoadedDataMeta, InvalidPackageStructure, LoaderRegistry, LoaderError


def packages_dir_resolver(meta: LoadedDataMeta) -> str:
    if os.path.isdir(os.path.join(meta.path, "packages")):
        return "packages"
    raise InvalidPackageStructure(meta, 'Folder "packages" must be present in directory root')


def main():
    CLI.setup()
    CLI.verbose_mode()
    CLI.print_info("Loading module using loader registry\n", ansi.Mod.BOLD)

    LoaderRegistry.target_dir = "generated"

    resource_meta = LoaderRegistry.load("github://corvis/esphome-packages", packages_dir_resolver)
    CLI.print_info(resource_meta.to_dict())

    base_dir = os.path.dirname(__file__)
    dir_asset_path = os.path.join(base_dir, "assets", "local-dir-asset")
    resource_meta = LoaderRegistry.load("local:" + dir_asset_path)
    CLI.print_info(resource_meta.to_dict())

    try:
        resource_meta = LoaderRegistry.load("something:blahblah")
    except LoaderError as e:
        CLI.print_error(e)


if __name__ == "__main__":
    main()
