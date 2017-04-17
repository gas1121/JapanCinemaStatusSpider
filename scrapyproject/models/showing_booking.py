from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy_utils import ArrowType
from sqlalchemy.orm import relationship
from scrapyproject.models.models import DeclarativeBase
from scrapyproject.models.showing import Showing


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

    def from_item(self, item):
        self.book_status = item['book_status']
        self.book_seat_count = item['book_seat_count']
        self.minutes_before = item['minutes_before']
        self.record_time = item['record_time']
        self.showing = Showing(**(item['showing']))
