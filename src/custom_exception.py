from contextlib import contextmanager
#from db.models.rome_model import RomeLabs

class MultiException(Exception):
    def __init__(self, db_client):
        self.db_client = db_client
        self.errors = []
        self.important_message = {
            "Insufficient Balance": "Balance",
            "Failed to perform, curl": "Proxy",
        }
        super().__init__()

    def custom_message(self, e):
        return self.important_message[e] if e in self.important_message else None


@contextmanager
def multi_exception_handler(pk, multi_exception, logger = None):
    try:
        yield multi_exception
    except Exception as e:
        custom_message = multi_exception.custom_message(e=e.args[0].split(':')[0])

        if not logger is None:
            logger.error(f"Custom error: {e}")

        if not custom_message is None:
            if not custom_message in multi_exception.errors:
                multi_exception.errors.append(custom_message)



def set_to_csv(s):
    return ','.join(map(str, s))
