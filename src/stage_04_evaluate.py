import argparse
import os
import logging
from src.utils import read_yaml, save_json
import numpy as np
import joblib
import math
import sklearn.metrics as metrics

STAGE = "EVALUATE"  ## <<< change stage name

logging.basicConfig(
    filename=os.path.join("logs", "running_logs.log"),
    level=logging.INFO,
    format="[%(asctime)s: %(levelname)s: %(module)s]: %(message)s",
    filemode="a",
)


def evaluate(config_path, params_path):
    ## read config files
    config = read_yaml(config_path)
    params = read_yaml(params_path)

    artifacts = config["artifacts"]

    model_dir = artifacts["MODEL_DIR"]
    model_dir_path = os.path.join(artifacts["ARTIFACTS_DIR"], model_dir)
    model_name = artifacts["MODEL_NAME"]
    model_path = os.path.join(model_dir_path, model_name)

    featurized_data_dir_path = os.path.join(
        artifacts["ARTIFACTS_DIR"], artifacts["FEATURIZED_DATA"]
    )
    featurized_test_data_path = os.path.join(
        featurized_data_dir_path, artifacts["FEATURIZED_DATA_TEST"]
    )

    model = joblib.load(model_path)
    matrix = joblib.load(featurized_test_data_path)

    labels = np.squeeze(matrix[:, 1].toarray())
    X = matrix[:, 2:]

    prediction_probabilities = model.predict_proba(X)
    pred = prediction_probabilities[:, 1]

    PRC_json_path = config["plots"]["PRC"]
    ROC_json_path = config["plots"]["ROC"]
    scores_json_path = config["metrics"]["SCORES"]

    avg_prec = metrics.average_precision_score(labels, pred)
    roc_auc = metrics.roc_auc_score(labels, pred)

    logging.info(f"len of labels: {len(labels)} and predictions: {len(pred)}")

    scores = {"avg_prc": avg_prec, "roc_auc": roc_auc}

    save_json(scores_json_path, scores)

    precisoin, recall, prc_theshold = metrics.precision_recall_curve(labels, pred)

    n_th_point = math.ceil(len(prc_theshold) / 1000)
    prc_points = list(zip(precisoin, recall, prc_theshold))[::n_th_point]

    logging.info(f"no of prc points: {len(prc_points)}")

    prc_data = {
        "prc": [{"precision": p, "recall": r, "threshold": t} for p, r, t in prc_points]
    }
    save_json(PRC_json_path, prc_data)

    fpr, tpr, roc_threshold = metrics.roc_curve(labels, pred)
    roc_points = zip(fpr, tpr, roc_threshold)

    roc_data = {
        "roc": [{"fpr": fp, "tpr": tp, "threshold": t} for fp, tp, t in roc_points]
    }

    logging.info(f"no of roc points: {len(list(roc_points))}")

    save_json(ROC_json_path, roc_data)


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", "-c", default="configs/config.yaml")
    args.add_argument("--params", "-p", default="params.yaml")
    parsed_args = args.parse_args()

    try:
        logging.info("\n********************")
        logging.info(f">>>>> stage {STAGE} started <<<<<")
        evaluate(config_path=parsed_args.config, params_path=parsed_args.params)
        logging.info(f">>>>> stage {STAGE} completed!<<<<<\n")
    except Exception as e:
        logging.exception(e)
        raise e
