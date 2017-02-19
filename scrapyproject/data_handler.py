import argparse
from scrapyproject import models
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func


def main():
    parser = argparse.ArgumentParser(
        description='Cinema booking data extract program.')
    parser.add_argument('--cinema', type=str, required=False,
                        help='target cinema')
    args = parser.parse_args()
    # firgure out movie booking status
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    book_seat_query = session.query(
        func.sum(models.Sessions.book_seat_count))
    total_seat_query = session.query(
        func.sum(models.Sessions.total_seat_count))
    if args.cinema is not None:
        book_seat_query = book_seat_query.filter(
            models.Sessions.cinema_name == args.cinema)
        total_seat_query = total_seat_query.filter(
            models.Sessions.cinema_name == args.cinema)
    book_seat_count, = book_seat_query.first()
    book_seat_count = 0 if book_seat_count is None else book_seat_count
    total_seat_count, = total_seat_query.first()
    total_seat_count = 0 if total_seat_count is None else total_seat_count
    session.close()
    title = args.cinema if args.cinema is not None else 'total'
    print("result: {0}: {1}/{2}".format(title, book_seat_count, total_seat_count))


if __name__ == '__main__':
    main()
