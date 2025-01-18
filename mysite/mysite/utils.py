def normalize_file_path(path):

    if path == '/':
        return path

    return f"/{path.strip('/')}"


def normalize_folder_path(path):

    if path == '/':
        return path

    return f"/{path.strip('/')}/"
