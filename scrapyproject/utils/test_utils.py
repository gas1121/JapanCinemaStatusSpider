import arrow


class TestUtil(object):
    def write_to_unique_html(text):
        """
        write content to unique html file
        """
        file_name = str(arrow.now().timestamp) + '.html'
        with open(file_name, 'w') as f:
            f.write(text)