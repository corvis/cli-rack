import os

from cli_rack import CLI, ansi
from cli_rack.loader import LocalLoader, LoadedDataMeta, InvalidPackageStructure


def components_dir_resolver(meta: LoadedDataMeta) -> str:
    if os.path.isdir(os.path.join(meta.path, 'components')):
        return 'components'
    raise InvalidPackageStructure(meta, "Folder \"components\" must be present in directory root")


def main():
    CLI.setup(show_stack_traces=True)
    CLI.print_info("Loading module from some local folder\n", ansi.Mod.BOLD)

    base_dir = os.path.dirname(__file__)
    loader = LocalLoader(target_dir='generated')
    single_file_asset_path = os.path.join(base_dir, 'assets', 'local-file-asset.txt')
    CLI.print_info('Loading single file asset from: ' + single_file_asset_path)
    resource_meta = loader.load('local:' + single_file_asset_path)
    CLI.print_info('\tDone')
    CLI.print_info(resource_meta.to_dict())

    dir_asset_path = os.path.join(base_dir, 'assets', 'local-dir-asset')
    CLI.print_info('Loading folder asset from: ' + dir_asset_path)
    resource_meta = loader.load('local:' + dir_asset_path, components_dir_resolver)
    CLI.print_info('\tDone')
    CLI.print_info(resource_meta.to_dict())


if __name__ == "__main__":
    main()
