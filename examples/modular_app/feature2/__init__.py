def is_available() -> bool:
    try:
        import jinja2

        return True
    except ImportError:
        return False
