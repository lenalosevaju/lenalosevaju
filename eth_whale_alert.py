import requests
import datetime
import matplotlib.pyplot as plt
import os

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
BASE_URL = "https://api.etherscan.io/api"
THRESHOLD_ETH = 500  # можно изменить порог

def get_block_number_by_timestamp(timestamp):
    params = {
        "module": "block",
        "action": "getblocknobytime",
        "timestamp": timestamp,
        "closest": "before",
        "apikey": ETHERSCAN_API_KEY
    }
    r = requests.get(BASE_URL, params=params)
    return int(r.json()["result"])

def get_transactions(start_block, end_block):
    page = 1
    txs = []
    while True:
        params = {
            "module": "account",
            "action": "txlist",
            "startblock": start_block,
            "endblock": end_block,
            "sort": "asc",
            "page": page,
            "offset": 1000,
            "apikey": ETHERSCAN_API_KEY
        }
        r = requests.get(BASE_URL, params=params)
        data = r.json()
        result = data.get("result", [])
        if not result:
            break
        txs.extend(result)
        page += 1
    return txs

def analyze_whales(days=5):
    whale_stats = {}
    for i in range(days):
        date = datetime.datetime.utcnow().date() - datetime.timedelta(days=i)
        start_time = int(datetime.datetime.combine(date, datetime.time.min).timestamp())
        end_time = int(datetime.datetime.combine(date, datetime.time.max).timestamp())
        start_block = get_block_number_by_timestamp(start_time)
        end_block = get_block_number_by_timestamp(end_time)
        print(f"🔍 Checking whales on {date} from block {start_block} to {end_block}")
        txs = get_transactions(start_block, end_block)
        whale_tx = [
            tx for tx in txs if float(tx["value"]) / 1e18 >= THRESHOLD_ETH and tx["isError"] == "0"
        ]
        whale_stats[str(date)] = {
            "count": len(whale_tx),
            "total_eth": sum(float(tx["value"]) / 1e18 for tx in whale_tx),
            "addresses": list(set(tx["from"] for tx in whale_tx))
        }
    return whale_stats

def plot(stats):
    dates = list(stats.keys())[::-1]
    counts = [stats[d]["count"] for d in dates]
    volumes = [stats[d]["total_eth"] for d in dates]

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.bar(dates, counts)
    plt.title("🐋 Whale TX Count")
    plt.xticks(rotation=45)

    plt.subplot(1, 2, 2)
    plt.plot(dates, volumes, marker="o")
    plt.title("📦 Total Whale ETH Moved")
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig("eth_whale_activity.png")
    plt.show()

if __name__ == "__main__":
    print("📊 Analyzing Ethereum whale activity...")
    stats = analyze_whales()
    for day, info in stats.items():
        print(f"{day}: {info['count']} whale TXs, total {info['total_eth']:.2f} ETH")
    plot(stats)
