from functools import lru_cache
from random import Random
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

PRIORITY = '核对提子'


def _vector(record):
    return [record['gap'], record['capture_claim'], int(record['repeat_move'])]


@lru_cache(maxsize=1)
def _model():
    rng=Random(441)
    signals=[]; labels=[]
    for case in range(90):
        category=case%3
        signals.append([rng.uniform(2,12)+category*4, rng.randint(0,1)+category*2, int(category==2)])
        labels.append(['正常',PRIORITY,'疑似重复落点'][category])
    train, hold, ytrain, yhold=train_test_split(signals,labels,test_size=.3,
                random_state=44,stratify=labels)
    pipeline=make_pipeline(StandardScaler(),SGDClassifier(loss='hinge',alpha=.01,random_state=44))
    pipeline.fit(train,ytrain)
    return pipeline, hold, yhold


def classify(records):
    if not records:
        return []
    pipeline, _, _=_model()
    queries=[_vector(record) for record in records]
    predicted=pipeline.predict(queries)
    margins=pipeline.decision_function(queries)
    classes=[str(name) for name in pipeline.classes_]
    priority=classes.index(PRIORITY) if PRIORITY in classes else 0
    return [{'label':str(label), 'score':round(float(margin[priority]),4)}
            for label, margin in zip(predicted, margins)]


def calculate(data):
    pipeline, hold, yhold=_model()
    query=[_vector(data['source'])]
    return {'label':str(pipeline.predict(query)[0]),'held_accuracy':round(float(pipeline.score(hold,yhold)),4),
            'margin':[round(float(x),4) for x in pipeline.decision_function(query)[0]],'n_holdout':len(hold)}
