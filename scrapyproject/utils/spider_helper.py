class CinemasDatabaseMixin:
    """
    mixin to make spider use database's cinemas table
    """
    use_cinemas_database = True


class SessionsDatabaseMixin:
    """
    mixin to make spider use database's sessions table
    """
    use_sessions_database = True


def use_cinemas_database(spider):
    return hasattr(spider, "use_cinemas_database")


def use_sessions_database(spider):
    return hasattr(spider, "use_sessions_database")
