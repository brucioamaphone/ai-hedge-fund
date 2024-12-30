from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize InfluxDB writer using environment variables
from influx_writer import InfluxWriter

writer = InfluxWriter()


# Example data (your actual data would come from your agents)
market_data = {
    "symbol": "VIRTUAL",
    "name": "Virtual Protocol",
    "creation_date": 1729527427000,
    "price": "$3.5800",
    "market_cap": "$3,581,461,872.00",
    "24h_volume": "$5,767,789.65",
    "liquidity": "$3,299,194.03",
    "24h_change": "6.75%",
    "trades_24h": "Buys: 1028, Sells: 508"
}

valuation_data = {
    "symbol": "VIRTUAL",
    "name": "Virtual Protocol",
    "mcap_tvl_analysis": {
        "signal": "bearish",
        "details": "Market Cap: $3,581,461,872.00, TVL: $3,299,194.03, Ratio: 1085.56"
    },
    "volume_mcap_analysis": {
        "signal": "bearish",
        "details": "24h Volume: $5,767,789.65, Volume/MCap Ratio: 0.002"
    }
}

risk_data = {
    "symbol": "VIRTUAL",
    "name": "Virtual Protocol",
    "liquidity_risk": {
        "signal": "medium_risk",
        "details": "Liquidity: $3,299,194.03, Volume/Liquidity Ratio: 1.75"
    },
    "volatility_risk": {
        "signal": "low_risk",
        "details": "1h Change: 0.53%, 24h Change: 6.75%"
    },
    "transaction_risk": {
        "signal": "medium_risk",
        "details": "Total Txns: 1536, Buy/Sell Ratio: 2.02"
    },
    "market_impact_risk": {
        "signal": "medium_risk",
        "details": "Avg Trade: $3,755.07, Max Trade: $32,991.94"
    },
    "position_limits": {
        "max_position": "$16,495.97",
        "risk_level": "medium_risk"
    }
}

portfolio_decision = {
    "symbol": "VIRTUAL",
    "name": "Virtual Protocol",
    "risk_assessment": {
        "max_position": "$0.00",
        "risk_level": "high_risk",
        "details": {}
    },
    "signal_analysis": {
        "bullish_signals": 0,
        "bearish_signals": 0,
        "weighted_score": "0.00",
        "base_action": "hold"
    },
    "final_decision": {
        "action": "hold",
        "size": "$0.00",
        "price": "$3.5800",
        "explanation": "Based on neutral weighted consensus (0.00) and high_risk risk assessment"
    }
}

def main():
    # Initialize InfluxDB writer using environment variables
    writer = InfluxWriter()

    token_address = "0x0b3e328455c4059EEb9e3f84b5543F74E24e7E1b"
    chain_id = "base"

    try:
        # Write all metrics
        writer.write_market_data(token_address, chain_id, market_data)
        writer.write_valuation_metrics(token_address, chain_id, valuation_data)
        writer.write_risk_metrics(token_address, chain_id, risk_data)
        writer.write_trading_decision(token_address, chain_id, portfolio_decision)
        
        print("Successfully wrote data to InfluxDB")
    except Exception as e:
        print(f"Error writing to InfluxDB: {e}")
    finally:
        writer.close()

if __name__ == "__main__":
    main()
