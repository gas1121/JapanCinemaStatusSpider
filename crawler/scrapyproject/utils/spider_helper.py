class CinemaDatabaseMixin:
    """
    mixin to make spider use database's cinema table
    """
    use_cinema_database = True


class ShowingDatabaseMixin:
    """
    mixin to make spider use database's showing table
    """
    use_showing_database = True


class MovieDatabaseMixin:
    """
    mixin to make spider use database's movie table
    """
    use_movie_database = True


def use_cinema_database(spider):
    return hasattr(spider, "use_cinema_database")


def use_showing_database(spider):
    return hasattr(spider, "use_showing_database")


def use_movie_database(spider):
    return hasattr(spider, "use_movie_database")
