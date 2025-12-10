import numpy as np
import pickle
import xgboost as xgb
import shap
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

# 加载模型与解释器（启动时加载一次）
model = xgb.XGBClassifier()
model.load_model("model.json")
explainer = shap.TreeExplainer(model)

# InfluxDB 配置（替换为实际地址）
client = InfluxDBClient(url="http://localhost:8086", token="your_token", org="monitor")
write_api = client.write_api(write_options=SYNCHRONOUS)

# 日志配置
logging.basicConfig(filename='monitor.log', level=logging.INFO)

def parse_and_process(raw_ bytes):
    try:
        # 步骤1：解析设备ID（假设前8字节为设备ID，十六进制）
        device_id = raw_data[:8].decode('ascii')
        payload = raw_data[8:].decode('ascii').strip()

        # 步骤2：解析传感器数据（假设格式： "1234,5678,9101"）
        values = list(map(int, payload.split(',')))
        # 转为物理量（示例：线性映射）
        signal = np.array(values) * 0.01  # 示例转换

        # 步骤3：特征提取（简化示例）
        rms = np.sqrt(np.mean(signal**2))
        kurt = np.mean(((signal - np.mean(signal)) / np.std(signal))**4)
        features = np.array([[rms, kurt]])  # 实际应包含更多特征

        # 步骤4：模型推理
        proba = model.predict_proba(features)[0]
        pred = model.predict(features)[0]
        label = ["normal", "deformation", "short"][pred]

        # 步骤5：SHAP解释（取第一个样本）
        shap_values = explainer.shap_values(features)[pred][0]

        # 步骤6：写入InfluxDB
        point = Point("transformer_status") \
            .tag("device_id", device_id) \
            .field("status", label) \
            .field("confidence", float(proba[pred])) \
            .field("rms", float(rms)) \
            .field("shap_rms", float(shap_values[0]))
        write_api.write(bucket="monitor", record=point)

        # 步骤7：预警判断
        if proba[pred] > 0.85 and label != "normal":
            logging.warning(f"ALERT: {device_id} -> {label} (conf: {proba[pred]:.2f})")

    except Exception as e:
        logging.error(f"Parse failed: {e}")