import argparse
import re
import unicodedata
from scrapyproject import models
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy import exists
import datetime


def main():
    parser = argparse.ArgumentParser(
        description='Cinema booking data extract program.')
    parser.add_argument('--file', type=str, required=False,
                        default="result.txt", help='result file name')
    parser.add_argument('--cinema', type=str, required=False,
                        help='target cinema')
    parser.add_argument('--merge', type=bool, required=False, default=False,
                        help='merge different version of same movie')
    args = parser.parse_args()
    # firgure out movie booking status
    engine = models.db_connect()
    session = sessionmaker(bind=engine)()
    book_count_label = func.sum(
        models.Sessions.book_seat_count).label("book_count")
    query = session.query(
        models.Sessions.title,
        book_count_label,
        func.sum(models.Sessions.total_seat_count),
        func.count(models.Sessions.id)
        ).group_by(models.Sessions.title).order_by(book_count_label.desc())
    if args.cinema is not None:
        query = query.filter(models.Sessions.cinema_name == args.cinema)
    result = {}
    for (title, book_seat_count, total_seat_count, count) in query.all():
        title = unicodedata.normalize('NFKC', title)
        cinema = args.cinema if args.cinema is not None else 'total'
        book_seat_count = 0 if book_seat_count is None else book_seat_count
        total_seat_count = 0 if total_seat_count is None else total_seat_count
        if args.merge:
            # remove movie version in title
            title = re.sub(r"^(.+)\((.+)\)$", r"\1", title)
            title = title.strip()
        if title not in result:
            result[title] = {}
            result[title]['cinema'] = cinema
            result[title]['book_seat_count'] = book_seat_count
            result[title]['total_seat_count'] = total_seat_count
            result[title]['count'] = count
        else:
            result[title]['book_seat_count'] += book_seat_count
            result[title]['total_seat_count'] += total_seat_count
            result[title]['count'] += count
    with open(args.file, 'w') as result_file:
        for title in result:
            cinema = result[title]['cinema']
            book_seat_count = result[title]['book_seat_count']
            total_seat_count = result[title]['total_seat_count']
            count = result[title]['count']
            percent = "{:.2%}".format(book_seat_count/(
                1 if not total_seat_count else total_seat_count))
            result_str = "{0} {1}: {2}/{3} {4} {5} times".format(
                title, cinema, book_seat_count, total_seat_count,
                percent, count)
            print(result_str)
            result_str += "\n"
            result_file.write(result_str)
    session.close()


if __name__ == '__main__':
    main()
