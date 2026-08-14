import argparse
import csv
import math

BAR_LENGTH = 10


class Line:
    def __init__(self, aggregate_trade_id, price, quantity, first_trade_id, last_trade_id, timestamp, is_buyer_maker, is_best_match):
        self.aggregate_trade_id = aggregate_trade_id
        self.price = price
        self.quantity = quantity
        self.first_trade_id = first_trade_id
        self.last_trade_id = last_trade_id
        self.timestamp = timestamp
        self.is_buyer_maker = is_buyer_maker
        self.is_best_match = is_best_match

        if is_buyer_maker:
            self.signed_transaction = -price * quantity
        else:
            self.signed_transaction = price * quantity

    def __str__(self):
        return (
            f"{self.aggregate_trade_id} "
            f"{self.price} "
            f"{self.quantity} "
            f"{self.first_trade_id} "
            f"{self.last_trade_id} "
            f"{self.timestamp} "
            f"{self.is_buyer_maker} "
            f"{self.is_best_match} "
            f"{self.signed_transaction}")


class ComputedData:
    def __init__(self, open_price, high, low, close, quote_volume, signed_quote_volume, aggressive_buy_volume, aggressive_sell_volume, imbalance, log_return, trade_count):
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.quote_volume = quote_volume
        self.signed_quote_volume = signed_quote_volume
        self.aggressive_buy_volume = aggressive_buy_volume
        self.aggressive_sell_volume = aggressive_sell_volume
        self.imbalance = imbalance
        self.log_return = log_return
        self.trade_count = trade_count

    def __str__(self):
        return (
            f"{self.__class__.__name__}("
            f"open={self.open}, "
            f"high={self.high}, "
            f"low={self.low}, "
            f"close={self.close}, "
            f"quote_volume={self.quote_volume}, "
            f"signed_quote_volume={self.signed_quote_volume}, "
            f"aggressive_buy_volume={self.aggressive_buy_volume}, "
            f"aggressive_sell_volume={self.aggressive_sell_volume}, "
            f"imbalance={self.imbalance}, "
            f"log_return={self.log_return}, "
            f"trade_count={self.trade_count}"
            f")"
        )


parser = argparse.ArgumentParser()

parser.add_argument(
    "--input",
    required=True,
    help="Csv to read"
)

parser.add_argument(
    "--output",
    required=True,
    help="Output file with new computed columns"
)

parser.add_argument(
    "--rows",
    required=False,
    type=int,
    help="Number of lines to process"
)

args = parser.parse_args()


with open(args.input, "r", encoding="utf-8", newline="") as input_file, \
     open(args.output, "w", encoding="utf-8", newline="") as output_file:

    reader = csv.reader(input_file)
    writer = csv.writer(output_file)

    writer.writerow([
        "open",
        "high",
        "low",
        "close",
        "quote_volume",
        "signed_quote_volume",
        "aggressive_buy_volume",
        "aggressive_sell_volume",
        "imbalance",
        "log_return",
        "trade_count"
    ])

    first_bar_start_ms = None
    interval_end = BAR_LENGTH

    open_price = 0
    high = 0
    low = math.inf
    quote_volume = 0
    signed_quote_volume = 0
    aggressive_buy_volume = 0
    aggressive_sell_volume = 0
    trade_count = 0

    lines = []

    last_computed_data = ComputedData(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    for number, csv_line in enumerate(reader, start=1):
        if args.rows is not None and number > args.rows:
            break

        timestamp_ms = int(csv_line[5])

        if first_bar_start_ms is None:
            # First bar Example : 70000 // 10000 -> 7 * (10000) = 70000
            first_bar_start_ms = (timestamp_ms // (BAR_LENGTH * 1000)) * (BAR_LENGTH * 1000)

        aggregate_trade_id = csv_line[0]
        price = float(csv_line[1])
        quantity = float(csv_line[2])
        first_trade_id = csv_line[3]
        last_trade_id = csv_line[4]

        normalized_timestamp_sec = (timestamp_ms - first_bar_start_ms) / 1000

        is_buyer_maker = csv_line[6].strip().lower() == "true"

        is_best_match = csv_line[7].strip().lower() == "true"

        line = Line(aggregate_trade_id, price, quantity, first_trade_id, last_trade_id, normalized_timestamp_sec, is_buyer_maker, is_best_match)
        print(line)

        # To jump empty intervals
        while normalized_timestamp_sec >= interval_end:
            if len(lines) < 1:
                previous_close = last_computed_data.close

                open_price = previous_close
                high = previous_close
                low = previous_close
                close = previous_close

                quote_volume = 0
                signed_quote_volume = 0
                aggressive_buy_volume = 0
                aggressive_sell_volume = 0
                imbalance = 0
                log_return = 0

            else:
                close = lines[-1].price

                if quote_volume != 0:
                    imbalance = signed_quote_volume / quote_volume
                else:
                    imbalance = 0

                if last_computed_data.close != 0:
                    log_return = math.log(close / last_computed_data.close)
                else:
                    log_return = 0

            computed_data = ComputedData(open_price, high, low, close, quote_volume, signed_quote_volume, aggressive_buy_volume, aggressive_sell_volume, imbalance, log_return, trade_count)


            writer.writerow([
                computed_data.open,
                computed_data.high,
                computed_data.low,
                computed_data.close,
                computed_data.quote_volume,
                computed_data.signed_quote_volume,
                computed_data.aggressive_buy_volume,
                computed_data.aggressive_sell_volume,
                computed_data.imbalance,
                computed_data.log_return,
                computed_data.trade_count
            ])

            print(computed_data)

            last_computed_data = computed_data

            # Reset for the new interval
            open_price = 0
            high = 0
            low = math.inf
            quote_volume = 0
            signed_quote_volume = 0
            aggressive_buy_volume = 0
            aggressive_sell_volume = 0
            trade_count = 0
            lines = []

            interval_end += BAR_LENGTH

        if len(lines) == 0:
            open_price = price

        if price > high:
            high = price

        if price < low:
            low = price

        transaction_volume = price * quantity

        quote_volume += transaction_volume
        signed_quote_volume += line.signed_transaction

        if line.signed_transaction < 0:
            aggressive_sell_volume += transaction_volume
        else:
            aggressive_buy_volume += transaction_volume

        lines.append(line)
        trade_count += 1

    # Save last bar
    if len(lines) > 0:
        close = lines[-1].price

        if quote_volume != 0:
            imbalance = signed_quote_volume / quote_volume
        else:
            imbalance = 0

        if last_computed_data.close != 0:
            log_return = math.log(close / last_computed_data.close)
        else:
            log_return = 0

        computed_data = ComputedData(open_price, high, low, close, quote_volume, signed_quote_volume, aggressive_buy_volume, aggressive_sell_volume, imbalance, log_return, trade_count)

        writer.writerow([
            computed_data.open,
            computed_data.high,
            computed_data.low,
            computed_data.close,
            computed_data.quote_volume,
            computed_data.signed_quote_volume,
            computed_data.aggressive_buy_volume,
            computed_data.aggressive_sell_volume,
            computed_data.imbalance,
            computed_data.log_return,
            computed_data.trade_count
        ])

        print(computed_data)