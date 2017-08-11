from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy_utils import ArrowType
from sqlalchemy.orm import relationship
import arrow

from models import DeclarativeBase
from models.showing import Showing


class ShowingBooking(DeclarativeBase):
    __tablename__ = "showing_booking"

    id = Column(Integer, primary_key=True)
    showing_id = Column(Integer, ForeignKey("showing.id"))
    showing = relationship("Showing")
    book_status = Column('book_status', String, nullable=False)
    book_seat_count = Column('book_seat_count', Integer, default=0,
                             nullable=False)
    minutes_before = Column('minutes_before', Integer, nullable=False)
    record_time = Column('record_time', ArrowType, nullable=False)

    @staticmethod
    def from_item(session, item):
        result = ShowingBooking()
        result.book_status = item['book_status']
        result.book_seat_count = item['book_seat_count']
        result.minutes_before = item['minutes_before']
        result.record_time = arrow.get(item['record_time'])
        result.showing = Showing.from_item(session, item['showing'])
        # if book_status is 'SoldOut', set book_seat_count
        if result.book_status == "SoldOut":
            result.book_seat_count = result.showing.total_seat_count
        return result
