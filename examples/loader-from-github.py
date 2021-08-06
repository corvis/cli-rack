import os

from cli_rack import CLI, ansi
from cli_rack.loader import LoadedDataMeta, InvalidPackageStructure, GithubLoader


def packages_dir_resolver(meta: LoadedDataMeta) -> str:
    if os.path.isdir(os.path.join(meta.path, "packages")):
        return "packages"
    raise InvalidPackageStructure(meta, 'Folder "packages" must be present in directory root')


def main():
    CLI.setup()
    CLI.verbose_mode()
    CLI.print_info("Loading module from GitHub repository\n", ansi.Mod.BOLD)

    loader = GithubLoader(target_dir="generated")
    locator = "github://corvis/esphome-packages"
    CLI.print_info("Loading assets from: " + locator)
    resource_meta = loader.load(locator, packages_dir_resolver)
    CLI.print_info("\tDone")
    CLI.print_info(resource_meta.to_dict())


if __name__ == "__main__":
    main()
