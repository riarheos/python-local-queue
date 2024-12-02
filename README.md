## python-local-queue

I got tired reimplementing a local queue running multiple tasks in parallel, so here it
goes in a Python module.

What to expect:

- Run work in parallel threads
- Threads can generate more work
- Any exception completely stops the queue

What to not expect:

- You need to be careful mangling data in your workers, probably you need your own locks (GIL may help here for simple
  cases but I wouldn't count on it)
- You need to set up logging to see per-thread info (see example.py for an example)

---

### Example

```python
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
```
