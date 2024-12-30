from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

# Get the project root directory (2 levels up from this file)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables with explicit path
load_dotenv(ROOT_DIR / '.env')

class InfluxWriter:
    def __init__(self):
        """Initialize InfluxDB client using environment variables"""
        self.url = os.getenv('INFLUXDB_URL')
        self.token = os.getenv('INFLUXDB_TOKEN')
        self.org = os.getenv('INFLUXDB_ORG')
        self.bucket = os.getenv('INFLUXDB_BUCKET')
        
        if not all([self.url, self.token, self.org, self.bucket]):
            missing = []
            if not self.url: missing.append("INFLUXDB_URL")
            if not self.token: missing.append("INFLUXDB_TOKEN")
            if not self.org: missing.append("INFLUXDB_ORG")
            if not self.bucket: missing.append("INFLUXDB_BUCKET")
            raise ValueError(f"Missing required InfluxDB environment variables: {', '.join(missing)}")
            
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def write_market_data(self, token_address: str, chain_id: str, data: dict):
        """Write market data metrics"""
        point = Point("market_data") \
            .tag("token", token_address) \
            .tag("chain", chain_id) \
            .tag("symbol", data["symbol"]) \
            .tag("name", data["name"]) \
            .field("creation_date", int(data["creation_date"])) \
            .field("price", float(data["price"].replace("$", ""))) \
            .field("market_cap", float(data["market_cap"].replace("$", "").replace(",", ""))) \
            .field("volume_24h", float(data["24h_volume"].replace("$", "").replace(",", ""))) \
            .field("liquidity", float(data["liquidity"].replace("$", "").replace(",", ""))) \
            .field("change_24h", float(data["24h_change"].replace("%", "").replace(",", ""))) \
            .field("buy_count", int(data["trades_24h"].split("Buys: ")[1].split(",")[0])) \
            .field("sell_count", int(data["trades_24h"].split("Sells: ")[1]))
        
        self.write_api.write(bucket=self.bucket, record=point)

    def write_technical_analysis(self, token_address: str, chain_id: str, data: dict):
        """Write technical analysis metrics"""
        timeframes = {
            "1h": {"momentum": -0.53, "volume": 60382.93, "buy_sell_ratio": 0.72},
            "6h": {"momentum": -2.46, "volume": 207766.41, "buy_sell_ratio": 1.42},
            "24h": {"momentum": 6.75, "volume": 240324.57, "buy_sell_ratio": 2.02}
        }
        
        for timeframe, metrics in timeframes.items():
            point = Point("technical_analysis") \
                .tag("token", token_address) \
                .tag("chain", chain_id) \
                .tag("symbol", data.get("symbol", "")) \
                .tag("name", data.get("name", "")) \
                .tag("timeframe", timeframe) \
                .field("momentum", metrics["momentum"]) \
                .field("volume", metrics["volume"]) \
                .field("buy_sell_ratio", metrics["buy_sell_ratio"])
            
            self.write_api.write(bucket=self.bucket, record=point)

    def write_valuation_metrics(self, token_address: str, chain_id: str, data: dict):
        """Write valuation metrics"""
        point = Point("valuation_metrics") \
            .tag("token", token_address) \
            .tag("chain", chain_id) \
            .tag("symbol", data.get("symbol", "")) \
            .tag("name", data.get("name", "")) \
            .field("mcap_tvl_ratio", float(data["mcap_tvl_analysis"]["details"].split("Ratio: ")[1])) \
            .field("volume_mcap_ratio", float(data["volume_mcap_analysis"]["details"].split("Ratio: ")[1]))
        
        self.write_api.write(bucket=self.bucket, record=point)

    def write_risk_metrics(self, token_address: str, chain_id: str, data: dict):
        """Write risk metrics"""
        point = Point("risk_metrics") \
            .tag("token", token_address) \
            .tag("chain", chain_id) \
            .tag("symbol", data["symbol"]) \
            .tag("name", data["name"]) \
            .field("liquidity_risk", data["liquidity_risk"]) \
            .field("volatility_risk", data["volatility_risk"]) \
            .field("transaction_risk", data["transaction_risk"]) \
            .field("market_impact_risk", data["market_impact_risk"]) \
            .field("max_position", float(data["max_position"]))
        
        self.write_api.write(bucket=self.bucket, record=point)

    def write_trading_decision(self, token_address: str, chain_id: str, data: dict):
        """Write trading decision"""
        point = Point("trading_decisions") \
            .tag("token", token_address) \
            .tag("chain", chain_id) \
            .tag("symbol", data.get("symbol", "")) \
            .tag("name", data.get("name", "")) \
            .field("action", data["final_decision"]["action"]) \
            .field("position_size", float(data["final_decision"]["size"].replace("$", "").replace(",", ""))) \
            .field("entry_price", float(data["final_decision"]["price"].replace("$", ""))) \
            .field("weighted_score", float(data["signal_analysis"]["weighted_score"])) \
            .field("risk_level", data["risk_assessment"]["risk_level"])
        
        self.write_api.write(bucket=self.bucket, record=point)

    def close(self):
        """Close the InfluxDB client"""
        self.client.close()
