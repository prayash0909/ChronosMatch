"""Run the asynchronous market simulator against the named Windows mmap queue."""
import argparse
import asyncio

from market_sim.simulator import HighThroughputSimulator
from shared_memory.buffer import SharedMemoryBuffer


async def _run(args):
    buffer = SharedMemoryBuffer(tag_name=args.tag_name)
    shutdown = [False]
    simulator = HighThroughputSimulator(
        buffer,
        target_orders_per_second=args.rate,
        seed=args.seed,
    )
    try:
        await simulator.generate_market_ticks(
            shutdown,
            max_orders=args.orders,
            report_every=args.report_every,
        )
    except KeyboardInterrupt:
        shutdown[0] = True
    finally:
        buffer.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rate", type=int, default=100_000, help="best-effort target orders/second")
    parser.add_argument("--orders", type=int, default=None, help="stop after this many accepted orders")
    parser.add_argument("--report-every", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--tag-name", default="Local\\ChronosMatchSharedBufferV3")
    args = parser.parse_args()
    if args.orders is not None and args.orders < 1:
        parser.error("--orders must be positive")
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
