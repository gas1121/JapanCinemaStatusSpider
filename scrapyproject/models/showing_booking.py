from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy_utils import ArrowType
from sqlalchemy.orm import relationship
from scrapyproject.models.models import DeclarativeBase


class ShowingBooking(DeclarativeBase):
    __tablename__ = "showing_booking"

    id = Column(Integer, primary_key=True)
    showing_id = Column(Integer, ForeignKey("showing.id"))
    showing = relationship("Showing")
    book_status = Column('book_status', String, nullable=False)
    book_seat_count = Column('book_seat_count', Integer, default=0,
                             nullable=False)
    record_time = Column('record_time', ArrowType, nullable=False)
