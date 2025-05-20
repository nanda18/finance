import unittest
from datetime import datetime, time, timedelta
from historicaldata import get_price_start_time, get_price_end_time

class TestGetPriceStartTime(unittest.TestCase):

    def test_within_trading_hours(self):
        # Test a time within trading hours
        board_time = datetime(2023, 10, 1, 10, 0)  # 10:00 AM
        result = get_price_start_time(board_time)
        self.assertEqual(result, board_time)

    def test_before_trading_hours(self):
        # Test a time before trading hours
        board_time = datetime(2023, 10, 1, 8, 0)  # 8:00 AM
        expected_result = datetime(2023, 9, 30, 15, 30)  # Previous day trading end time
        result = get_price_start_time(board_time)
        self.assertEqual(result, expected_result)

    def test_after_trading_hours(self):
        # Test a time after trading hours
        board_time = datetime(2023, 10, 1, 16, 0)  # 4:00 PM
        expected_result = datetime(2023, 10, 1, 15, 30)  # Current day trading end time
        result = get_price_start_time(board_time)
        self.assertEqual(result, expected_result)

class TestGetPriceEndTime(unittest.TestCase):

    def test_normal_case(self):
        # Test a start time within trading hours
        start_time = datetime(2024, 5, 14, 9, 30)  # 9:30 AM
        expected_end_time = start_time + timedelta(minutes=40)  # 10:10 AM
        result = get_price_end_time(start_time)
        self.assertEqual(result, expected_end_time)

    def test_end_time_within_trading_hours(self):
        # Test a start time that results in an end time within trading hours
        start_time = datetime(2024, 5, 14, 10, 0)  # 10:00 AM
        expected_end_time = start_time + timedelta(minutes=40)  # 10:40 AM
        result = get_price_end_time(start_time)
        self.assertEqual(result, expected_end_time)

    def test_end_time_exceeds_trading_hours(self):
        # Test a start time that results in an end time exceeding trading hours
        start_time = datetime(2024, 5, 14, 15, 0)  # 3:00 PM
        expected_end_time = datetime.combine(start_time.date(), time(15, 30))  # 3:30 PM
        result = get_price_end_time(start_time)
        self.assertEqual(result, expected_end_time)

    def test_start_time_after_trading_hours(self):
        # Test a start time after trading hours
        start_time = datetime(2024, 5, 14, 16, 0)  # 4:00 PM
        expected_end_time = datetime.combine(start_time.date() + timedelta(days=1), time(9, 30))  # Next day's 9:30 AM
        result = get_price_end_time(start_time)
        self.assertEqual(result, expected_end_time)

if __name__ == '__main__':
    unittest.main()