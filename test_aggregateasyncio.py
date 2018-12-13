import asyncio
import unittest
from unittest import mock
from aggregateasyncio import wait_with_optional


class TestWaitWithOptional(unittest.TestCase):
    # region Helpers
    TIMEOUT_REQUIRED = 1
    TIMEOUT_OPTIONAL = 0.5

    DELAY_IMMEDIATE = 0
    DELAY_FAST = 0.1
    DELAY_MEDIUM = 0.350
    DELAY_SLOW = 0.650
    DELAY_SLOWER = 0.750
    DELAY_GLACIAL = 2

    async def create_task_(self, tag, delay, exception):
        if exception is None:
            if delay == self.DELAY_IMMEDIATE:
                return tag
            else:
                await asyncio.sleep(delay)
                return tag
        else:
            if delay == self.DELAY_IMMEDIATE:
                raise exception
            else:
                await asyncio.sleep(delay)
                raise exception

    def create_task(self, tag, delay, exception=None):
        return asyncio.create_task(self.create_task_(tag, delay, exception))

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def AsyncMock(self, *args, **kwargs):
        m = mock.MagicMock(*args, **kwargs)

        async def mock_coro(*args, **kwargs):
            return m(*args, **kwargs)

        mock_coro.mock = m
        return mock_coro

    async def _test_wait(self, requiredArgs, optionalArgs):
        return await wait_with_optional(
            [self.create_task(*args) for args in requiredArgs],
            self.TIMEOUT_REQUIRED,
            [self.create_task(*args) for args in optionalArgs],
            self.TIMEOUT_OPTIONAL
        )

    def _result_from_future(self, future):
        if future.cancelled() or not future.done():
            return None

        result = None
        exception = None

        if not future.exception():
            result = future.result()
        else:
            exception = future.exception()

        return {
            'result': result,
            'exception': exception
        }

    def _test(self, expected, requiredArgs, optionalArgs):
        required, optional = self._run(
            self._test_wait(requiredArgs, optionalArgs))
        self.assertEqual([self._result_from_future(future)
                          for future in required], expected['required'])
        self.assertEqual([self._result_from_future(future)
                          for future in optional], expected['optional'])
    # endregion

    # region Tests for required tasks
    def test_1_required_immediate(self):
        self._test({
            'required': [
                {
                    'result': 'immediate',
                    'exception': None
                }
            ],
            'optional': []
        },
            [('immediate', self.DELAY_IMMEDIATE)],
            [])

    def test_1_required_slow(self):
        self._test({
            'required': [
                {
                    'result': 'slow',
                    'exception': None
                }
            ],
            'optional': []
        },
            [('slow', self.DELAY_SLOW)],
            [])

    def test_1_required_glacial(self):
        self._test({
            'required': [
                None
            ],
            'optional': []
        },
            [('glacial', self.DELAY_GLACIAL)],
            [])

    def test_3_required(self):
        self._test({
            'required': [
                {
                    'result': 'slow',
                    'exception': None,
                },
                None,
                {
                    'result': 'fast',
                    'exception': None,
                }
            ],
            'optional': []
        },
            [
                ('slow', self.DELAY_SLOW),
                ('glacial', self.DELAY_GLACIAL),
                ('fast', self.DELAY_FAST)
        ],
            [])
    # endregion

    # region Tests for optonal tasks
    def test_1_optional_fast(self):
        self._test({
            'required': [],
            'optional': [
                {
                    'result': 'fast',
                    'exception': None,
                },
            ]
        },
            [],
            [('fast', self.DELAY_FAST)])

    def test_1_optional_slow(self):
        self._test({
            'required': [],
            'optional': [None]
        },
            [],
            [('slow', self.DELAY_SLOW)])

    def test_3_optional(self):
        self._test({
            'required': [],
            'optional': [
                {
                    'result': 'fast',
                    'exception': None,
                },
                None,
                {
                    'result': 'immediate',
                    'exception': None,
                },
            ]
        },
            [],
            [
                ('fast', self.DELAY_FAST),
                ('slow', self.DELAY_SLOW),
                ('immediate', self.DELAY_IMMEDIATE)
        ])
    # endregion

    # region Tests for mixed (required and optional) casks
    def test_1_required_fast_1_optional_fast(self):
        self._test({
            'required': [
                {
                    'result': 'fast 1',
                    'exception': None,
                },
            ],
            'optional': [
                {
                    'result': 'fast 2',
                    'exception': None,
                },
            ]
        },
            [
                ('fast 1', self.DELAY_FAST),
        ],
            [
                ('fast 2', self.DELAY_FAST),
        ])

    def test_1_required_fast_1_optional_slow(self):
        self._test({
            'required': [
                {
                    'result': 'fast',
                    'exception': None,
                },
            ],
            'optional': [
                None,
            ]
        },
            [
                ('fast', self.DELAY_FAST),
        ],
            [
                ('slow', self.DELAY_SLOW),
        ])

    def test_1_required_slow_1_optional_slower(self):
        self._test({
            'required': [
                {
                    'result': 'slow',
                    'exception': None,
                },
            ],
            'optional': [
                None,
            ]
        },
            [
                ('slow', self.DELAY_SLOW),
        ],
            [
                ('slower', self.DELAY_SLOWER),
        ])

    def test_1_required_slower_1_optional_slow(self):
        self._test({
            'required': [
                {
                    'result': 'slower',
                    'exception': None,
                },
            ],
            'optional': [
                {
                    'result': 'slow',
                    'exception': None,
                }
            ]
        },
            [
                ('slower', self.DELAY_SLOWER),
        ],
            [
                ('slow', self.DELAY_SLOW),
        ])

    def test_1_required_fast_1_required_slower_1_optional_slow(self):
        self._test({
            'required': [
                {
                    'result': 'slower',
                    'exception': None,
                },
                {
                    'result': 'fast',
                    'exception': None,
                },
            ],
            'optional': [
                {
                    'result': 'slow',
                    'exception': None,
                }
            ]
        },
            [
                ('slower', self.DELAY_SLOWER),
                ('fast', self.DELAY_FAST)
        ],
            [
                ('slow', self.DELAY_SLOW),
        ])
    # endregion

    # region Tests for failed tasks
    def test_1_required_fast_fail_1_optional_fast(self):
        exp = Exception('fast 1')
        self._test({
            'required': [
                {
                    'result': None,
                    'exception': exp,
                },
            ],
            'optional': [
                {
                    'result': 'fast 2',
                    'exception': None,
                }
            ]
        },
            [
                ('fast 1', self.DELAY_FAST, exp)
        ],
            [
                ('fast 2', self.DELAY_FAST),
        ])
    # endregion
