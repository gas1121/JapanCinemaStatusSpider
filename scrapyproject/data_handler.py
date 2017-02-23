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
    query = session.query(
        models.Sessions.title,
        func.sum(models.Sessions.book_seat_count),
        func.sum(models.Sessions.total_seat_count),
        func.count(models.Sessions.id)
        ).group_by(models.Sessions.title)
    if args.cinema is not None:
        query = query.filter(models.Sessions.cinema_name == args.cinema)
    for (title, book_seat_count, total_seat_count, count) in query.all():
        cinema = args.cinema if args.cinema is not None else 'total'
        book_seat_count = 0 if book_seat_count is None else book_seat_count
        total_seat_count = 0 if total_seat_count is None else total_seat_count
        print("result: {0} {1}: {2}/{3} {4} times".format(
            title, cinema, book_seat_count, total_seat_count, count))
    session.close()


if __name__ == '__main__':
    main()
