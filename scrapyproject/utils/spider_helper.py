class CinemasDatabaseMixin:
    """
    mixin to make spider use database's cinemas table
    """
    use_cinemas_database = True


class ShowingsDatabaseMixin:
    """
    mixin to make spider use database's showings table
    """
    use_showings_database = True


def use_cinemas_database(spider):
    return hasattr(spider, "use_cinemas_database")


def use_showings_database(spider):
    return hasattr(spider, "use_showings_database")
