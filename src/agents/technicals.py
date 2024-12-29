import math
from typing import Dict

from langchain_core.messages import HumanMessage

from agents.state import AgentState, show_agent_reasoning

import json
import pandas as pd
import numpy as np

from tools.dexscreener_api import prices_to_df


##### Technical Analyst #####
def technical_analyst_agent(state: AgentState):
    """
    Technical analysis system adapted for DEX trading with focus on:
    1. Price Momentum
    2. Volume Analysis
    3. Buy/Sell Pressure
    4. Liquidity Trends
    """
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    pair_info = data["pair_info"]
    
    # Initialize signals and reasoning
    signals = []
    reasoning = {}
    
    # 1. Price Momentum Analysis
    momentum_score = 0
    price_change_24h = float(pair_info['priceChange']['h24'])
    price_change_6h = float(pair_info['priceChange']['h6'])
    price_change_1h = float(pair_info['priceChange']['h1'])
    
    # Check different timeframes for momentum
    if price_change_1h > 0:
        momentum_score += 1
    if price_change_6h > 0:
        momentum_score += 1
    if price_change_24h > 0:
        momentum_score += 1
        
    signals.append('bullish' if momentum_score >= 2 else 'bearish' if momentum_score == 0 else 'neutral')
    reasoning["momentum_signal"] = {
        "signal": signals[0],
        "details": f"1h: {price_change_1h:.2f}%, 6h: {price_change_6h:.2f}%, 24h: {price_change_24h:.2f}%"
    }
    
    # 2. Volume Analysis
    volume_score = 0
    volume_1h = float(pair_info['volume']['h1'])
    volume_6h = float(pair_info['volume']['h6'])
    volume_24h = float(pair_info['volume']['h24'])
    
    # Check if volume is increasing
    hourly_avg_24h = volume_24h / 24
    hourly_avg_6h = volume_6h / 6
    hourly_volume_1h = volume_1h
    
    if hourly_volume_1h > hourly_avg_6h:
        volume_score += 1
    if hourly_avg_6h > hourly_avg_24h:
        volume_score += 1
        
    signals.append('bullish' if volume_score >= 2 else 'bearish' if volume_score == 0 else 'neutral')
    reasoning["volume_signal"] = {
        "signal": signals[1],
        "details": f"1h Vol: ${volume_1h:,.2f}, 6h Avg: ${hourly_avg_6h:,.2f}, 24h Avg: ${hourly_avg_24h:,.2f}"
    }
    
    # 3. Buy/Sell Pressure Analysis
    pressure_score = 0
    buys_1h = pair_info['txns']['h1']['buys']
    sells_1h = pair_info['txns']['h1']['sells']
    buys_6h = pair_info['txns']['h6']['buys']
    sells_6h = pair_info['txns']['h6']['sells']
    buys_24h = pair_info['txns']['h24']['buys']
    sells_24h = pair_info['txns']['h24']['sells']
    
    # Calculate buy/sell ratios
    ratio_1h = buys_1h / sells_1h if sells_1h > 0 else 1
    ratio_6h = buys_6h / sells_6h if sells_6h > 0 else 1
    ratio_24h = buys_24h / sells_24h if sells_24h > 0 else 1
    
    if ratio_1h > 1.1:  # 10% more buys than sells
        pressure_score += 1
    if ratio_6h > 1.1:
        pressure_score += 1
    if ratio_24h > 1.1:
        pressure_score += 1
        
    signals.append('bullish' if pressure_score >= 2 else 'bearish' if pressure_score == 0 else 'neutral')
    reasoning["pressure_signal"] = {
        "signal": signals[2],
        "details": f"1h B/S: {ratio_1h:.2f}, 6h B/S: {ratio_6h:.2f}, 24h B/S: {ratio_24h:.2f}"
    }
    
    # Aggregate signals
    bullish_count = len([s for s in signals if s == 'bullish'])
    bearish_count = len([s for s in signals if s == 'bearish'])
    
    if bullish_count > len(signals) / 2:
        final_signal = 'bullish'
    elif bearish_count > len(signals) / 2:
        final_signal = 'bearish'
    else:
        final_signal = 'neutral'
        
    if show_reasoning:
        print("\nTechnical Analysis:")
        print(json.dumps(reasoning, indent=2))
        
    # Update state
    state["signals"] = state.get("signals", {})
    state["reasoning"] = state.get("reasoning", {})
    state["signals"]["technical"] = final_signal
    state["reasoning"]["technical"] = reasoning
    
    return state

def calculate_trend_signals(prices_df):
    """
    Advanced trend following strategy using multiple timeframes and indicators
    """
    # Calculate EMAs for multiple timeframes
    ema_8 = calculate_ema(prices_df, 8)
    ema_21 = calculate_ema(prices_df, 21)
    ema_55 = calculate_ema(prices_df, 55)
    
    # Calculate ADX for trend strength
    adx = calculate_adx(prices_df, 14)
    
    # Calculate Ichimoku Cloud
    ichimoku = calculate_ichimoku(prices_df)
    
    # Determine trend direction and strength
    short_trend = ema_8 > ema_21
    medium_trend = ema_21 > ema_55
    
    # Combine signals with confidence weighting
    trend_strength = adx['adx'].iloc[-1] / 100.0
    
    if short_trend.iloc[-1] and medium_trend.iloc[-1]:
        signal = 'bullish'
        confidence = trend_strength
    elif not short_trend.iloc[-1] and not medium_trend.iloc[-1]:
        signal = 'bearish'
        confidence = trend_strength
    else:
        signal = 'neutral'
        confidence = 0.5
    
    return {
        'signal': signal,
        'confidence': confidence,
        'metrics': {
            'adx': float(adx['adx'].iloc[-1]),
            'trend_strength': float(trend_strength),
            # 'ichimoku': ichimoku
        }
    }

def calculate_mean_reversion_signals(prices_df):
    """
    Mean reversion strategy using statistical measures and Bollinger Bands
    """
    # Calculate z-score of price relative to moving average
    ma_50 = prices_df['close'].rolling(window=50).mean()
    std_50 = prices_df['close'].rolling(window=50).std()
    z_score = (prices_df['close'] - ma_50) / std_50
    
    # Calculate Bollinger Bands
    bb_upper, bb_lower = calculate_bollinger_bands(prices_df)
    
    # Calculate RSI with multiple timeframes
    rsi_14 = calculate_rsi(prices_df, 14)
    rsi_28 = calculate_rsi(prices_df, 28)
    
    # Mean reversion signals
    extreme_z_score = abs(z_score.iloc[-1]) > 2
    price_vs_bb = (prices_df['close'].iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
    
    # Combine signals
    if z_score.iloc[-1] < -2 and price_vs_bb < 0.2:
        signal = 'bullish'
        confidence = min(abs(z_score.iloc[-1]) / 4, 1.0)
    elif z_score.iloc[-1] > 2 and price_vs_bb > 0.8:
        signal = 'bearish'
        confidence = min(abs(z_score.iloc[-1]) / 4, 1.0)
    else:
        signal = 'neutral'
        confidence = 0.5
    
    return {
        'signal': signal,
        'confidence': confidence,
        'metrics': {
            'z_score': float(z_score.iloc[-1]),
            'price_vs_bb': float(price_vs_bb),
            'rsi_14': float(rsi_14.iloc[-1]),
            'rsi_28': float(rsi_28.iloc[-1])
        }
    }

def calculate_momentum_signals(prices_df):
    """
    Multi-factor momentum strategy
    """
    # Price momentum
    returns = prices_df['close'].pct_change()
    mom_1m = returns.rolling(21).sum()
    mom_3m = returns.rolling(63).sum()
    mom_6m = returns.rolling(126).sum()
    
    # Volume momentum
    volume_ma = prices_df['volume'].rolling(21).mean()
    volume_momentum = prices_df['volume'] / volume_ma
    
    # Relative strength
    # (would compare to market/sector in real implementation)
    
    # Calculate momentum score
    momentum_score = (
        0.4 * mom_1m +
        0.3 * mom_3m +
        0.3 * mom_6m
    ).iloc[-1]
    
    # Volume confirmation
    volume_confirmation = volume_momentum.iloc[-1] > 1.0
    
    if momentum_score > 0.05 and volume_confirmation:
        signal = 'bullish'
        confidence = min(abs(momentum_score) * 5, 1.0)
    elif momentum_score < -0.05 and volume_confirmation:
        signal = 'bearish'
        confidence = min(abs(momentum_score) * 5, 1.0)
    else:
        signal = 'neutral'
        confidence = 0.5
    
    return {
        'signal': signal,
        'confidence': confidence,
        'metrics': {
            'momentum_1m': float(mom_1m.iloc[-1]),
            'momentum_3m': float(mom_3m.iloc[-1]),
            'momentum_6m': float(mom_6m.iloc[-1]),
            'volume_momentum': float(volume_momentum.iloc[-1])
        }
    }

def calculate_volatility_signals(prices_df):
    """
    Volatility-based trading strategy
    """
    # Calculate various volatility metrics
    returns = prices_df['close'].pct_change()
    
    # Historical volatility
    hist_vol = returns.rolling(21).std() * math.sqrt(252)
    
    # Volatility regime detection
    vol_ma = hist_vol.rolling(63).mean()
    vol_regime = hist_vol / vol_ma
    
    # Volatility mean reversion
    vol_z_score = (hist_vol - vol_ma) / hist_vol.rolling(63).std()
    
    # ATR ratio
    atr = calculate_atr(prices_df)
    atr_ratio = atr / prices_df['close']
    
    # Generate signal based on volatility regime
    current_vol_regime = vol_regime.iloc[-1]
    vol_z = vol_z_score.iloc[-1]
    
    if current_vol_regime < 0.8 and vol_z < -1:
        signal = 'bullish'  # Low vol regime, potential for expansion
        confidence = min(abs(vol_z) / 3, 1.0)
    elif current_vol_regime > 1.2 and vol_z > 1:
        signal = 'bearish'  # High vol regime, potential for contraction
        confidence = min(abs(vol_z) / 3, 1.0)
    else:
        signal = 'neutral'
        confidence = 0.5
    
    return {
        'signal': signal,
        'confidence': confidence,
        'metrics': {
            'historical_volatility': float(hist_vol.iloc[-1]),
            'volatility_regime': float(current_vol_regime),
            'volatility_z_score': float(vol_z),
            'atr_ratio': float(atr_ratio.iloc[-1])
        }
    }

def calculate_stat_arb_signals(prices_df):
    """
    Statistical arbitrage signals based on price action analysis
    """
    # Calculate price distribution statistics
    returns = prices_df['close'].pct_change()
    
    # Skewness and kurtosis
    skew = returns.rolling(63).skew()
    kurt = returns.rolling(63).kurt()
    
    # Test for mean reversion using Hurst exponent
    hurst = calculate_hurst_exponent(prices_df['close'])
    
    # Correlation analysis
    # (would include correlation with related securities in real implementation)
    
    # Generate signal based on statistical properties
    if hurst < 0.4 and skew.iloc[-1] > 1:
        signal = 'bullish'
        confidence = (0.5 - hurst) * 2
    elif hurst < 0.4 and skew.iloc[-1] < -1:
        signal = 'bearish'
        confidence = (0.5 - hurst) * 2
    else:
        signal = 'neutral'
        confidence = 0.5
    
    return {
        'signal': signal,
        'confidence': confidence,
        'metrics': {
            'hurst_exponent': float(hurst),
            'skewness': float(skew.iloc[-1]),
            'kurtosis': float(kurt.iloc[-1])
        }
    }

def weighted_signal_combination(signals, weights):
    """
    Combines multiple trading signals using a weighted approach
    """
    # Convert signals to numeric values
    signal_values = {
        'bullish': 1,
        'neutral': 0,
        'bearish': -1
    }
    
    weighted_sum = 0
    total_confidence = 0
    
    for strategy, signal in signals.items():
        numeric_signal = signal_values[signal['signal']]
        weight = weights[strategy]
        confidence = signal['confidence']
        
        weighted_sum += numeric_signal * weight * confidence
        total_confidence += weight * confidence
    
    # Normalize the weighted sum
    if total_confidence > 0:
        final_score = weighted_sum / total_confidence
    else:
        final_score = 0
    
    # Convert back to signal
    if final_score > 0.2:
        signal = 'bullish'
    elif final_score < -0.2:
        signal = 'bearish'
    else:
        signal = 'neutral'
    
    return {
        'signal': signal,
        'confidence': abs(final_score)
    }

def normalize_pandas(obj):
    """Convert pandas Series/DataFrames to primitive Python types"""
    if isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, dict):
        return {k: normalize_pandas(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [normalize_pandas(item) for item in obj]
    return obj

def calculate_macd(prices_df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    ema_12 = prices_df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = prices_df['close'].ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, signal_line

def calculate_rsi(prices_df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = prices_df['close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(
    prices_df: pd.DataFrame,
    window: int = 20
) -> tuple[pd.Series, pd.Series]:
    sma = prices_df['close'].rolling(window).mean()
    std_dev = prices_df['close'].rolling(window).std()
    upper_band = sma + (std_dev * 2)
    lower_band = sma - (std_dev * 2)
    return upper_band, lower_band

def calculate_ema(df: pd.DataFrame, window: int) -> pd.Series:
    """
    Calculate Exponential Moving Average
    
    Args:
        df: DataFrame with price data
        window: EMA period
    
    Returns:
        pd.Series: EMA values
    """
    return df['close'].ewm(span=window, adjust=False).mean()

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Average Directional Index (ADX)
    
    Args:
        df: DataFrame with OHLC data
        period: Period for calculations
    
    Returns:
        DataFrame with ADX values
    """
    # Calculate True Range
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift())
    df['low_close'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    
    # Calculate Directional Movement
    df['up_move'] = df['high'] - df['high'].shift()
    df['down_move'] = df['low'].shift() - df['low']
    
    df['plus_dm'] = np.where(
        (df['up_move'] > df['down_move']) & (df['up_move'] > 0),
        df['up_move'],
        0
    )
    df['minus_dm'] = np.where(
        (df['down_move'] > df['up_move']) & (df['down_move'] > 0),
        df['down_move'],
        0
    )
    
    # Calculate ADX
    df['+di'] = 100 * (df['plus_dm'].ewm(span=period).mean() / 
                       df['tr'].ewm(span=period).mean())
    df['-di'] = 100 * (df['minus_dm'].ewm(span=period).mean() / 
                       df['tr'].ewm(span=period).mean())
    df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
    df['adx'] = df['dx'].ewm(span=period).mean()
    
    return df[['adx', '+di', '-di']]

def calculate_ichimoku(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Calculate Ichimoku Cloud indicators
    
    Args:
        df: DataFrame with OHLC data
    
    Returns:
        Dictionary containing Ichimoku components
    """
    # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
    period9_high = df['high'].rolling(window=9).max()
    period9_low = df['low'].rolling(window=9).min()
    tenkan_sen = (period9_high + period9_low) / 2

    # Kijun-sen (Base Line): (26-period high + 26-period low)/2
    period26_high = df['high'].rolling(window=26).max()
    period26_low = df['low'].rolling(window=26).min()
    kijun_sen = (period26_high + period26_low) / 2

    # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)

    # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
    period52_high = df['high'].rolling(window=52).max()
    period52_low = df['low'].rolling(window=52).min()
    senkou_span_b = ((period52_high + period52_low) / 2).shift(26)

    # Chikou Span (Lagging Span): Close shifted back 26 periods
    chikou_span = df['close'].shift(-26)

    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    }

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range
    
    Args:
        df: DataFrame with OHLC data
        period: Period for ATR calculation
    
    Returns:
        pd.Series: ATR values
    """
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    
    return true_range.rolling(period).mean()

def calculate_hurst_exponent(price_series: pd.Series, max_lag: int = 20) -> float:
    """
    Calculate Hurst Exponent to determine long-term memory of time series
    H < 0.5: Mean reverting series
    H = 0.5: Random walk
    H > 0.5: Trending series
    
    Args:
        price_series: Array-like price data
        max_lag: Maximum lag for R/S calculation
    
    Returns:
        float: Hurst exponent
    """
    lags = range(2, max_lag)
    # Add small epsilon to avoid log(0)
    tau = [max(1e-8, np.sqrt(np.std(np.subtract(price_series[lag:], price_series[:-lag])))) for lag in lags]
    
    # Return the Hurst exponent from linear fit
    try:
        reg = np.polyfit(np.log(lags), np.log(tau), 1)
        return reg[0] # Hurst exponent is the slope
    except (ValueError, RuntimeWarning):
        # Return 0.5 (random walk) if calculation fails
        return 0.5

def calculate_obv(prices_df: pd.DataFrame) -> pd.Series:
    obv = [0]
    for i in range(1, len(prices_df)):
        if prices_df['close'].iloc[i] > prices_df['close'].iloc[i - 1]:
            obv.append(obv[-1] + prices_df['volume'].iloc[i])
        elif prices_df['close'].iloc[i] < prices_df['close'].iloc[i - 1]:
            obv.append(obv[-1] - prices_df['volume'].iloc[i])
        else:
            obv.append(obv[-1])
    prices_df['OBV'] = obv
    return prices_df['OBV']
