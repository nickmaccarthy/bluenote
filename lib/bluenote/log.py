import os
import logging
import logging.handlers as logging_handler

class logger(object):


    def get_logger(self, name='bluenote'):

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        BN_HOME = os.environ.get('BN_HOME')

        LOG_FILENAME = os.path.join(BN_HOME, 'var', 'log', 'bluenote.log')

        # clear any built up log handlers
        if self.logger.handlers:
            self.logger.handlers = []

        handler = logging_handler.RotatingFileHandler(LOG_FILENAME, maxBytes=102400, backupCount=5)
        log_format = logging.Formatter("%(asctime)s [%(levelname)-s] - [%(name)s] - [%(module)s] - %(message)s")
        handler.setFormatter(log_format)
        self.logger.addHandler(handler)

        return self.logger

