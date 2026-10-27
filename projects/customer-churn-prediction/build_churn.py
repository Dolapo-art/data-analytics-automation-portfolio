"""Reproducible IBM sample churn classification. New AI-assisted portfolio rebuild."""
from pathlib import Path
import hashlib, json, platform
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix, precision_recall_curve)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
SEED = 42
SOURCE = 'https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv'

def evaluate(y, probabilities, threshold):
    predicted = (probabilities >= threshold).astype(int)
    return dict(accuracy=float(accuracy_score(y, predicted)),
        precision=float(precision_score(y, predicted, zero_division=0)),
        recall=float(recall_score(y, predicted, zero_division=0)),
        f1=float(f1_score(y, predicted, zero_division=0)),
        roc_auc=float(roc_auc_score(y, probabilities)),
        average_precision=float(average_precision_score(y, probabilities)),
        confusion_matrix=confusion_matrix(y, predicted, labels=[0,1]).tolist())

def run():
    raw_path = ROOT / 'telco_raw.csv'
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == '16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91', 'Unexpected source file; review provenance before running'
    raw = pd.read_csv(raw_path)
    assert raw.customerID.is_unique and raw.Churn.isin(['Yes','No']).all()
    df = raw.copy()
    for col in df.select_dtypes('object'):
        df[col] = df[col].str.strip()
    df['TotalCharges'] = pd.to_numeric(df.TotalCharges, errors='coerce')
    df['ChurnFlag'] = df.Churn.eq('Yes').astype(int)
    df['TenureBand'] = pd.cut(df.tenure, [-1,12,24,48,72], labels=['0–12 months','13–24 months','25–48 months','49–72 months']).astype(str)
    # Exclude IDs, target/derived target, reporting bands and demographic attributes.
    excluded = ['customerID','Churn','ChurnFlag','TenureBand','gender','SeniorCitizen','Partner','Dependents']
    X = df.drop(columns=excluded)
    y = df.ChurnFlag
    train, other = train_test_split(df.index, test_size=.4, stratify=y, random_state=SEED)
    valid, test = train_test_split(other, test_size=.5, stratify=y.loc[other], random_state=SEED)
    assert not(set(train)&set(valid) or set(train)&set(test) or set(valid)&set(test))
    assert len(train)+len(valid)+len(test)==len(df)
    num = ['tenure','MonthlyCharges','TotalCharges']
    cat = [c for c in X if c not in num]
    prep = ColumnTransformer([
        ('numeric', Pipeline([('impute',SimpleImputer(strategy='median')),('scale',StandardScaler())]),num),
        ('category',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore'))]),cat)])
    model = Pipeline([('preprocess',prep),('model',LogisticRegression(max_iter=2000, random_state=SEED))])
    model.fit(X.loc[train], y.loc[train])
    # Choose decision threshold on validation F1, never on held-out test labels.
    val_probs = model.predict_proba(X.loc[valid])[:,1]
    choices = [(float(t),float(f1_score(y.loc[valid], val_probs >= t))) for t in np.linspace(.15,.70,56)]
    threshold, val_f1 = max(choices, key=lambda item:(item[1], item[0]))
    test_probs = model.predict_proba(X.loc[test])[:,1]
    baseline = DummyClassifier(strategy='prior').fit(X.loc[train],y.loc[train])
    baseline_probs = baseline.predict_proba(X.loc[test])[:,1]
    result = dict(seed=SEED, source=SOURCE, source_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        rows=len(df), churned=int(y.sum()), observed_churn_rate=float(y.mean()),
        blank_total_charges=int(df.TotalCharges.isna().sum()),
        split_sizes=dict(train=len(train),validation=len(valid),test=len(test)),
        threshold=threshold, threshold_selection='Maximum validation F1; tie breaks toward higher threshold',
        validation_f1=val_f1, baseline=evaluate(y.loc[test],baseline_probs,.5),
        test=evaluate(y.loc[test],test_probs,threshold), test_at_0_5=evaluate(y.loc[test],test_probs,.5),
        feature_columns=list(X.columns), excluded_columns=excluded,
        versions=dict(python=platform.python_version(),pandas=pd.__version__,numpy=np.__version__,sklearn=sklearn.__version__))
    df.to_csv(ROOT/'customers_clean.csv', index=False)
    split = pd.Series('train',index=df.index); split.loc[valid]='validation';split.loc[test]='test'
    pd.DataFrame({'customerID':df.customerID,'split':split}).to_csv(ROOT/'split_manifest.csv',index=False)
    holdout=df.loc[test,['customerID','Contract','InternetService','TenureBand','MonthlyCharges','ChurnFlag']].copy()
    holdout['churn_probability']=test_probs
    holdout['predicted_churn']=(test_probs>=threshold).astype(int)
    holdout.to_csv(ROOT/'holdout_predictions.csv',index=False)
    (ROOT/'metrics.json').write_text(json.dumps(result,indent=2))
    # Independent cohort summaries: observed sample, not out-of-sample predictions.
    cohorts=[]
    for dimension in ['Contract','InternetService','TenureBand']:
        t=df.groupby(dimension,observed=True).ChurnFlag.agg(['count','sum','mean']).reset_index()
        t.columns=['segment','customers','churned','churn_rate'];t.insert(0,'dimension',dimension);cohorts.append(t)
    segments=pd.concat(cohorts,ignore_index=True)
    segments.to_csv(ROOT/'segment_summary.csv',index=False)
    assert int(segments[segments.dimension.eq('Contract')].customers.sum())==len(df)
    assert sum(sum(r) for r in result['test']['confusion_matrix'])==len(test)
    draw_dashboard(df,segments,result,y.loc[test],test_probs)
    payload=dict(customers=df[['Contract','InternetService','TenureBand','MonthlyCharges','ChurnFlag']].to_dict('records'),metrics=result)
    template=(ROOT/'dashboard_template.html').read_text()
    (ROOT/'dashboard.html').write_text(template.replace('__DATA_JSON__',json.dumps(payload,ensure_ascii=False).replace('</','<\\/')))
    write_notebook(result)
    print(json.dumps(result,indent=2))
    return result

def draw_dashboard(df,segments,result,y_test,probs):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig=plt.figure(figsize=(15,10),facecolor='#F3F6FA')
    fig.text(.06,.95,'CUSTOMER RETENTION  /  IBM PUBLIC SAMPLE',color='#147D87',weight='bold',size=12)
    fig.text(.06,.90,'Churn patterns & model evaluation',color='#183349',weight='bold',size=25)
    metrics=[('CUSTOMERS',f'{len(df):,}'),('OBSERVED CHURN',f'{df.ChurnFlag.mean():.1%}'),('TEST ROC–AUC',f"{result['test']['roc_auc']:.3f}"),('TEST CHURN RECALL',f"{result['test']['recall']:.1%}")]
    for i,(label,value) in enumerate(metrics):
        ax=fig.add_axes([.06+i*.235,.76,.215,.105],facecolor='white');ax.set_xticks([]);ax.set_yticks([])
        for s in ax.spines.values():s.set_visible(False)
        ax.text(.06,.73,label,color='#677C90',size=10);ax.text(.06,.20,value,color='#183349',size=23,weight='bold')
    for dim,pos,title in [('Contract',[.08,.44,.38,.25],'Observed churn by contract'),('TenureBand',[.56,.44,.37,.25],'Observed churn by tenure')]:
        ax=fig.add_axes(pos,facecolor='white');rows=segments[segments.dimension.eq(dim)]
        ax.barh(rows.segment,rows.churn_rate*100,color='#147D87');ax.set_xlim(0,55);ax.set_xlabel('Churn rate (%)');ax.set_title(title,loc='left',weight='bold',pad=15)
        ax.invert_yaxis()
        for j,r in enumerate(rows.itertuples()):ax.text(r.churn_rate*100+1,j,f'{r.churn_rate:.1%}  (n={r.customers:,})',va='center',size=9)
    ax=fig.add_axes([.08,.10,.38,.24],facecolor='white');cm=np.array(result['test']['confusion_matrix'])
    ax.imshow(cm,cmap='Blues');ax.set_xticks([0,1],['Predicted stay','Predicted churn']);ax.set_yticks([0,1],['Actual stay','Actual churn']);ax.set_title('Held-out test confusion matrix',loc='left',weight='bold',pad=15)
    for i in range(2):
        for j in range(2):ax.text(j,i,str(cm[i,j]),ha='center',va='center',size=17,color='white' if cm[i,j]>cm.max()/2 else '#183349')
    ax=fig.add_axes([.56,.10,.37,.24],facecolor='white');prec,rec,_=precision_recall_curve(y_test,probs)
    ax.plot(rec,prec,color='#147D87',lw=2);ax.axhline(y_test.mean(),ls='--',color='#8899AA',label='Test prevalence');ax.set_xlabel('Churn recall');ax.set_ylabel('Precision');ax.set_title('Held-out test precision–recall',loc='left',weight='bold',pad=15);ax.legend(frameon=False,fontsize=9)
    fig.text(.06,.035,'DOLAPO ADENIYI  |  New AI-assisted rebuild • fictional sample • snapshot classification, not a prospective churn forecast',color='#677C90',size=9)
    fig.savefig(ROOT/'churn_dashboard.png',dpi=140,bbox_inches='tight');plt.close(fig)

def write_notebook(result):
    def md(text):return dict(cell_type='markdown',metadata={},source=text.splitlines(True))
    code='from build_churn import run\nresults = run()\nresults["test"]\n'
    cells=[md('# Customer Churn Classification — Dolapo Adeniyi\nNew AI-assisted portfolio rebuild using IBM’s public fictional telco sample. This does not reproduce the historical CV project or validate its reported 85% accuracy.\n\n## Method\nA stratified 60/20/20 split separates training, threshold selection and test evaluation. Median imputation and one-hot encoding fit only on training customers. Logistic regression is compared with a majority-class baseline. F1 threshold selection uses validation only. No test-set tuning or refitting occurs.\n\nRun this notebook from its project directory after installing requirements.txt.'),
       dict(cell_type='code',execution_count=None,metadata={},source=code.splitlines(True),outputs=[]),
       md('## Measured script-run results\nThe pipeline was executed through build_churn.py; this notebook is a rerunnable entry point and has not been separately executed in a notebook kernel.\n\n```json\n'+json.dumps(result['test'],indent=2)+'\n```'),
       md('## Dashboard\n![Observed churn and test evaluation](churn_dashboard.png)\n\nOpen dashboard.html for contract, internet-service and tenure filters. Cohort charts describe the complete sample; model metrics use the fixed held-out test split and do not change with filters.\n\n## Interpretation and limits\nObserved differences are associations, not causal effects. Labels refer to churn already observed in a snapshot; scoring does not establish a future prediction horizon. Retention interventions require prospective validation, consent and an experiment before claiming churn reduction. See README.md for measured results and source attribution.')]
    notebook=dict(nbformat=4,nbformat_minor=5,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},cells=cells)
    for i,cell in enumerate(cells):cell['id']=f'churn-{i}'
    (ROOT/'churn_analysis.ipynb').write_text(json.dumps(notebook,indent=2,ensure_ascii=False))

if __name__=='__main__':run()
