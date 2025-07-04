"""Test script to demonstrate the logging transition."""

import logging
import sys

sys.path.insert(0, "src")

import nexar


def test_logging_levels():
    """Test different logging levels."""
    print("=== Testing Logging Levels ===")

    # Test INFO level
    print("\n1. INFO Level Logging:")
    nexar.configure_logging(logging.INFO)
    client = nexar.NexarClient(
        riot_api_key="fake-key",
        default_v4_region=nexar.RegionV4.NA1,
        default_v5_region=nexar.RegionV5.AMERICAS,
        cache_config=nexar.SMART_CACHE_CONFIG,
    )

    # Test DEBUG level
    print("\n2. DEBUG Level Logging:")
    nexar.configure_logging(logging.DEBUG)
    client2 = nexar.NexarClient(
        riot_api_key="fake-key",
        default_v4_region=nexar.RegionV4.NA1,
        default_v5_region=nexar.RegionV5.AMERICAS,
        cache_config=nexar.SMART_CACHE_CONFIG,
    )

    # Test stats functionality
    print("\n3. Statistics functionality:")
    print("Initial stats:", client.get_api_call_stats())
    client.print_api_call_summary()

    print("\n=== All Tests Passed! ===")


if __name__ == "__main__":
    test_logging_levels()
