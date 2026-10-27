"""Independent checks on split ownership and reported evaluation, without retraining."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, average_precision_score
p=Path(__file__).resolve().parent
m=json.loads((p/'metrics.json').read_text())
data=pd.read_csv(p/'customers_clean.csv'); split=pd.read_csv(p/'split_manifest.csv'); holdout=pd.read_csv(p/'holdout_predictions.csv')
assert split.customerID.is_unique and set(split.customerID)==set(data.customerID)
assert set(split.loc[split.split.eq('test'),'customerID'])==set(holdout.customerID)
assert len(data)==7043 and int(data.ChurnFlag.sum())==m['churned']
y=holdout.ChurnFlag; probs=holdout.churn_probability; pred=(probs>=m['threshold']).astype(int)
assert np.array_equal(pred,holdout.predicted_churn)
for metric,fn in [('accuracy',accuracy_score),('precision',precision_score),('recall',recall_score),('f1',f1_score)]:
 assert abs(fn(y,pred)-m['test'][metric])<1e-12,metric
for metric,fn in [('roc_auc',roc_auc_score),('average_precision',average_precision_score)]:
 assert abs(fn(y,probs)-m['test'][metric])<1e-12,metric
assert confusion_matrix(y,pred).tolist()==m['test']['confusion_matrix']
assert m['feature_columns']==['tenure','PhoneService','MultipleLines','InternetService','OnlineSecurity','OnlineBackup','DeviceProtection','TechSupport','StreamingTV','StreamingMovies','Contract','PaperlessBilling','PaymentMethod','MonthlyCharges','TotalCharges']
assert 'ChurnFlag' not in m['feature_columns'] and 'customerID' not in m['feature_columns']
print('PASS: split coverage, test isolation, confusion matrix and all six metrics independently recomputed.')
