import os


def get_abs_path(project_path: str) -> str:
    """Returns the absolute path given relative path.

    Args:
        project_path (str): path starting with top-level directory.

    Returns:
        str: absolute path

    Examples:
    >>> get_abs_path("rent_buy_invest/configs")
    '/Users/FooBarUser/rent_buy_invest/configs'
    """
    # TODO do not hardcode this
    if not project_path.startswith("rent_buy_invest"):
        raise ValueError("Invalid project_path")
    # TODO move this line to be a constant?
    dir_containing_top_level_dir = os.path.join(
        os.path.join(os.path.dirname(__file__), ".."), ".."
    )
    dir_containing_top_level_dir = os.path.abspath(dir_containing_top_level_dir)
    return os.path.join(os.path.abspath(dir_containing_top_level_dir), project_path)
