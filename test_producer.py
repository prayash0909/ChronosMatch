
import time
from shared_memory.buffer import SharedMemoryBuffer


def main():
    buffer = SharedMemoryBuffer()

    try:
        # First SELL order: 3 units at 100
        buffer.write_order(2001, 100.0, 3, b"S")
        print("Sent SELL: ID=2001, Price=100, Qty=3")
        time.sleep(1)

        # Second SELL order: 4 units at 100
        buffer.write_order(2002, 100.0, 4, b"S")
        print("Sent SELL: ID=2002, Price=100, Qty=4")
        time.sleep(1)

        # BUY order: 6 units at 100
        buffer.write_order(2003, 100.0, 6, b"B")
        print("Sent BUY: ID=2003, Price=100, Qty=6")
        time.sleep(1)

    finally:
        buffer.close()


if __name__ == "__main__":
    main()
