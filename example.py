import logging
import logging.config

from LocalQueue import LocalQueue


class Foo:
    def __init__(self, kind: str):
        self.kind = kind

    def work(self, queue: LocalQueue, arg: int) -> None:
        logging.info('I am doing %s work with arg %d', self.kind, arg)

        # enqueue more work to do
        for _ in range(arg):
            queue.add_work(self.work, arg - 1)


def bar(queue: LocalQueue, info: str) -> None:
    logging.info('This was passed via kwargs: %s', info)


def main():
    # Initialize the queue
    queue = LocalQueue(5)

    # Add some initial work
    foo = Foo('amazing')
    queue.add_work(foo.work, 3)
    queue.add_work(bar, info='kwargs are working too')

    # Run and wait for completion
    queue.run()


if __name__ == '__main__':
    loggingConfig = {
        "version": 1,
        "loggers": {
            "": {
                "level": "DEBUG",
                "handlers": [
                    "console"
                ]
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "std",
                "stream": "ext://sys.stdout"
            }
        },
        "formatters": {
            "std": {
                "format": "%(asctime)s  %(levelname)10s  %(name)10s  %(threadName)30s  %(message)s"
            }
        }
    }

    logging.config.dictConfig(loggingConfig)
    main()
