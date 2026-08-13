# Order Flow Resilience

This project tests a simple market microstructure strategy on ETHUSDT.

The strategy looks for strong selling pressure that no longer pushes the price down. This may show that large buyers are absorbing the sell orders and that the price could rebound.

BTCUSDT is used as a market reference to remove general market movements.

## Data

Historical Binance Spot aggregated trades can be downloaded here:

* [BTCUSDT aggTrades](https://data.binance.vision/?prefix=data/spot/monthly/aggTrades/BTCUSDT/)
* [ETHUSDT aggTrades](https://data.binance.vision/?prefix=data/spot/monthly/aggTrades/ETHUSDT/)

Download the monthly ZIP files and extract them in data/raw/ before running the strategy.
