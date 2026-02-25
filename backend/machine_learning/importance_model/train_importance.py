import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


def train_and_save_model():
    base_path = os.path.dirname(__file__)
    data_path = os.path.join(base_path, "training_data.csv")
    model_output = os.path.join(base_path, "importance_model.joblib")

    df = pd.read_csv(data_path)

    # X = Features (cat_id, is_work, temp, rain, etc.)
    # y = Target (importance_score)
    X = df.drop("importance_score", axis=1)
    y = df["importance_score"]

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    joblib.dump(model, model_output)
    print(f"Model saved to {model_output}")


if __name__ == "__main__":
    train_and_save_model()
