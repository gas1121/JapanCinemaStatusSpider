from enum import Enum
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_, cast
from scrapyproject.models.models import DeclarativeBase, db_connect


class Cinema(DeclarativeBase):
    __tablename__ = "cinema"

    id = Column(Integer, primary_key=True)
    # name may differ depends on crawled site, so we collect all names
    # in order to make query easier.
    names = Column('names', ARRAY(String), nullable=False)
    county = Column('county', String, nullable=False)
    company = Column('company', String)
    site = Column('site', String)
    # screens are handled as same as names
    screens = Column('screens', JSONB, nullable=False)
    # as screens may contain multiple versions of single screen,
    # we use next two column to help identify a cinema
    screen_count = Column('screen_count', Integer, nullable=False)
    total_seats = Column('total_seats', Integer, nullable=False)
    # site that data mainly crawled from
    source = Column('source', String, nullable=False)

    @staticmethod
    def get_cinema_if_exist(item):
        """
        Get cinema if it already exists in database, otherwise return None

        As data crawled from those sites often differs between each other,
        we have several rules to use to find exist cinema:
        - first of all, same "county", then:
        - have "site", same "site";
        - have name in "names", same name in "names";
        Some cinemas may be treated as different cinemas when crawled from
        different site but we will leave them there now.
        """
        engine = db_connect()
        session = sessionmaker(bind=engine)()
        query = session.query(Cinema).filter(and_(
            Cinema.county == item.county, or_(
                and_(item.site is not None, Cinema.site == item.site),
                and_(item.names is not None, Cinema.names.overlap(
                    cast(item.names, ARRAY(String))))
            )))
        result = query.first()
        session.close()
        return result

    @staticmethod
    def get_by_name(cinema_name):
        engine = db_connect()
        session = sessionmaker(bind=engine)()
        query = session.query(Cinema).filter(
            Cinema.names.any(cinema_name)
        )
        cinema = query.first()
        session.close()
        return cinema

    class MergeMethod(Enum):
        info_only = 1  # update names and screens only
        update_count = 2  # also update screen count and total seat number
        replace = 3  # replace all data

    def merge(self, new_cinema, merge_method):
        """
        merge data from new crawled cinema data depends on strategy
        """
        if merge_method == self.MergeMethod.info_only:
            self.names.extend(x for x in new_cinema.names if
                              x not in self.names)
            new_cinema.screens.update(self.screens)
            self.screens = new_cinema.screens
        elif merge_method == self.MergeMethod.update_count:
            self.names.extend(x for x in new_cinema.names if
                              x not in self.names)
            for new_screen in new_cinema.screens:
                if new_screen not in self.screens:
                    curr_seat_count = int(new_cinema.screens[new_screen])
                    self.screens[new_screen] = curr_seat_count
                    self.screen_count += 1
                    self.total_seats += curr_seat_count
        else:
            new_cinema.id = self.id
            self = new_cinema
