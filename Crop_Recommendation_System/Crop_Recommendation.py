import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import pickle

data = pd.read_csv('Crop_recommendation.csv')

X = data.drop('Label', axis=1)
y = data['Label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2)

classifier_rf = RandomForestClassifier(n_estimators= 10, criterion="entropy")  
classifier_rf.fit(X_train, y_train) 

y_pred = classifier_rf.predict(X_test)

pickle.dump(classifier_rf, open('model.pkl', 'wb'))