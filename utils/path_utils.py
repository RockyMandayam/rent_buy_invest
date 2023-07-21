import os


def get_abs_path(project_path: str) -> str:
    """Returns the absolute path given relative path.

    Args:
        project_path (str): path starting with top-level directory.

    Returns:
        str: absolute path

    Examples:
    >>> get_abs_path("rent-buy-invest/configs")
    '/Users/FooBarUser/rent-buy-invest/configs'
    """
    if not project_path.startswith("rent-buy-invest"):
        raise ValueError("Invalid project_path")
    # TODO move this line to be a constant?
    dir_containing_top_level_dir = os.path.join(
        os.path.join(os.path.dirname(__file__), ".."), ".."
    )
    dir_containing_top_level_dir = os.path.abspath(dir_containing_top_level_dir)
    return os.path.join(os.path.abspath(dir_containing_top_level_dir), project_path)
