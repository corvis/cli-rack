from cli_rack.modular import ExtensionUnavailableError


def is_available() -> bool:
    try:
        import jinja2

        return True
    except ImportError:
        raise ExtensionUnavailableError(
            "modular_app.feature2", "Jinja2 is required but it is not installed"
        ).hint_install_python_package("jinja2")
