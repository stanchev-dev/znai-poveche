from django.db import connection
from django.db.utils import OperationalError, ProgrammingError


def profile_has_avatar_column() -> bool:
    table_name = "accounts_profile"
    try:
        with connection.cursor() as cursor:
            description = connection.introspection.get_table_description(cursor, table_name)
    except (OperationalError, ProgrammingError):
        return False

    column_names = {col.name for col in description}
    return "avatar" in column_names
