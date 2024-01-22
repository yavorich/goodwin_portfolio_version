from rest_framework.exceptions import ValidationError


def validate_file_size(file, mb=4):
    """Установить ограничение для загружаемых файлов"""
    if not file:
        return
    max_size = mb * 1024 * 1024
    if file.size > max_size:
        raise ValidationError(f"Размер файла не должен превышать {mb} МБ.")
