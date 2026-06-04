# -*- coding: utf-8 -*-
"""
GitHub Actions 版本 - 天气数据采集脚本
每小时从 Open-Meteo API 抓取未来 24h 预报快照
数据存为 JSON 文件: data/YYYY-MM-DD/HH.json

地点: 中国浙江省杭州市钱塘区 (30.30N, 120.49E)
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta

import requests

# ====== 配置 ======
LAT = 30.30
LON = 120.49
TZ = "Asia/Shanghai"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

HOURLY_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "shortwave_radiation",
    "direct_radiation",
    "diffuse_radiation",
    "et0_fao_evapotranspiration",
    "sunshine_duration",
]

URL = "https://api.open-meteo.com/v1/forecast"


def fetch_forecast() -> dict:
    """从 Open-Meteo 获取未来 24h 预报"""
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": ",".join(HOURLY_PARAMS),
        "timezone": TZ,
        "forecast_hours": 24,
        "models": "best_match",
    }
    resp = requests.get(URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def save_snapshot(data: dict) -> str:
    """保存快照为 JSON 文件，返回文件路径"""
    now = datetime.now(timezone(timedelta(hours=8)))  # UTC+8

    # 目录结构: data/YYYY-MM-DD/
    date_dir = os.path.join(DATA_DIR, now.strftime("%Y-%m-%d"))
    os.makedirs(date_dir, exist_ok=True)

    # 文件名: HH.json (如 14.json)
    filename = now.strftime("%H") + ".json"
    filepath = os.path.join(date_dir, filename)

    # 构建快照数据结构
    snapshot = {
        "fetch_time_utc8": now.strftime("%Y-%m-%d %H:%M:%S"),
        "fetch_timestamp": now.isoformat(),
        "location": {
            "name": "杭州钱塘区",
            "lat": LAT,
            "lon": LON,
        },
        "forecast_hours": 24,
        "hourly": data["hourly"],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    return filepath


def main():
    """主函数 - 被 GitHub Actions 每小时调用一次"""
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 开始抓取天气数据...")

    try:
        data = fetch_forecast()
        filepath = save_snapshot(data)

        # 统计
        total_files = 0
        for root, dirs, files in os.walk(DATA_DIR):
            total_files += len([f for f in files if f.endswith(".json")])

        print(f"  [OK] 保存至: {filepath}")
        print(f"  [OK] 累计快照文件: {total_files}")
        print(f"  [OK] 温度范围: {min(data['hourly']['temperature_2m']):.1f} ~ "
              f"{max(data['hourly']['temperature_2m']):.1f} C")
        print(f"  [OK] 峰值GHI: {max(data['hourly']['shortwave_radiation']):.0f} W/m2")
        print(f"  [OK] 总降水量: {sum(data['hourly']['precipitation']):.1f} mm")

    except Exception as e:
        print(f"  [ERR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
