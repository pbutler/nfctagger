# nfctagger

NFC Tag Reading and Writing Library

## Introduction

This library provides a simple way to read and write NFC tags.  At first
it will focus on using the ACR122U reader, with NTAG21x tags.  It will
be extended to support other readers and tags in the future as I gain
access to relevant readers and tags.

## Motivations

* At this point nfcpy which is a great library, is not being
  maintained(?) and it's support for ACR122U is not working.  
* pyscard, the other library that supports ACR122U is very low level and
  does not handle much directly i.e. working with NDEF messages, handling
  specific operations.  In the end, it requires a lot of knowledge of
  the NFC protocol to use it.  Removing that barrier is the goal of this
  library.

## Prerequisites

This library uses pyscard to talk to the card reader.  So it requires a
properly working pyscard installation including a `pcscd` daemon
running.

## Installation

Once this library is published, it will be available on PyPI and can be
installed with pip:

```bash
pip install nfctagger
```

## Usage

Right now after installation you can either use it as a library or as a command line tool to overwrite an NTAG215 with a hello world message

```bash
python -mnfctagger
```

To use the library in your code, you can use the following example:

```python
from nfctagger import PCSCWaiter

waiter = PCSCWaiter()

ncards = 0
while True:
    # wait for a card to be detected for 1 second
    connection = waiter.get_next_connection(timeout=1)
    if connection is None:
        continue
    handle(connection)
return 0
```

## Development

This library uses the `uv` program to manage the virtual environment
and dependencies. Imports should follow the order `reorder-python-imports`.
