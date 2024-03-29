"""
    Me incomoda mucho trabajar con Jupyter así que haré
    un solo archivo aquí que tenga todo
"""

# Aquí importamos las librerías, hay que instalarlas primero uwu
# Se usan pandas, shutil, sklearn, os, numpy ...

import pandas as pd
import shutil

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import confusion_matrix, cohen_kappa_score, classification_report, accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

import os
import numpy as np


# Con lo anterior listo, ahora necesitamos guardar los datos, como vamos a usar
# data de github, hay que conseguir los csv! (se va a demorar un poco)

train = {
    'anger': pd.read_csv('https://raw.githubusercontent.com/dccuchile/CC6205/master/assignments/assignment_1/data/train/anger-train.txt', sep='\t', names=['id', 'tweet', 'class', 'sentiment_intensity']),
    'fear': pd.read_csv('https://raw.githubusercontent.com/dccuchile/CC6205/master/assignments/assignment_1/data/train/fear-train.txt', sep='\t', names=['id', 'tweet', 'class', 'sentiment_intensity']),
    'joy': pd.read_csv('https://raw.githubusercontent.com/dccuchile/CC6205/master/assignments/assignment_1/data/train/joy-train.txt', sep='\t', names=['id', 'tweet', 'class', 'sentiment_intensity']),
    'sadness': pd.read_csv('https://raw.githubusercontent.com/dccuchile/CC6205/master/assignments/assignment_1/data/train/sadness-train.txt', sep='\t', names=['id', 'tweet', 'class', 'sentiment_intensity'])
}

target = {
    'anger': pd.read_csv('https://raw.githubusercontent.com/dccuchile/CC6205/master/assignments/assignment_1/data/target/anger-target.txt', sep='\t', names=['id', 'tweet', 'class', 'sentiment_intensity'], na_values=['NONE']),
    'fear': pd.read_csv('https://raw.githubusercontent.com/dccuchile/CC6205/master/assignments/assignment_1/data/target/fear-target.txt', sep='\t', names=['id', 'tweet', 'class', 'sentiment_intensity'], na_values=['NONE']),
    'joy': pd.read_csv('https://raw.githubusercontent.com/dccuchile/CC6205/master/assignments/assignment_1/data/target/joy-target.txt', sep='\t', names=['id', 'tweet', 'class', 'sentiment_intensity'], na_values=['NONE']),
    'sadness': pd.read_csv('https://raw.githubusercontent.com/dccuchile/CC6205/master/assignments/assignment_1/data/target/sadness-target.txt', sep='\t', names=['id', 'tweet', 'class', 'sentiment_intensity'], na_values=['NONE'])
}



# Lo que sigue debería imprimir la cantidad de tweets en cada
# dataset:

def get_group_dist(group_name, train):
    print(group_name, "\n",
          train[group_name].groupby('sentiment_intensity').count())

def print_qtweets(dataset):
    for key in dataset:
        get_group_dist(key, dataset)

#print_qtweets(train)


# Esto es la métrica de evaluación
# NO SE MODIFICA ESTO ;-;

def auc(test_set, predicted_set):
    high_predicted = np.array([prediction[2] for prediction in predicted_set])
    medium_predicted = np.array(
        [prediction[1] for prediction in predicted_set])
    low_predicted = np.array([prediction[0] for prediction in predicted_set])

    high_test = np.where(test_set == 'high', 1.0, 0.0)
    medium_test = np.where(test_set == 'medium', 1.0, 0.0)
    low_test = np.where(test_set == 'low', 1.0, 0.0)

    auc_high = roc_auc_score(high_test, high_predicted)
    auc_med = roc_auc_score(medium_test, medium_predicted)
    auc_low = roc_auc_score(low_test, low_predicted)

    auc_w = (low_test.sum() * auc_low + medium_test.sum() * auc_med +
             high_test.sum() * auc_high) / (
                 low_test.sum() + medium_test.sum() + high_test.sum())
    return auc_w    



# Aquí se supone que el dataset se divide en train y test
def split_dataset(dataset):
    # Dividir el dataset en train set y test set
    X_train, X_test, y_train, y_test = train_test_split(
        dataset.tweet,
        dataset.sentiment_intensity,
        shuffle=True,
        test_size=0.33)
    return X_train, X_test, y_train, y_test

# CLASIFICADOR, Aquí hay que meter mano y modificar cosas, actualmente se usa
# naive-bayes.
# Definimos el pipeline con el vectorizador y el clasificador.

# Esto hace los tokens para un tweet (considera emojis y caritas)
# y ademas añade un negado a todo lo que venga después de una negación

# Remueve stop words, puntos, comas, dos puntos y tags de twitter
from nltk.corpus import stopwords
def remStopWords(tokens):
    newTokens = []
    stopWords = set(stopwords.words('english'))
    stopWords_extended = stopWords | {'.', ',', ':', '+', '-', '(',')',';','\'','..','...','—', '>','<','\\','n'}
    for token in tokens:
        if (token not in stopWords_extended) and (token[0:1]!='@'):
            newTokens.append(token)
    return newTokens

# Hace un stemming
from nltk.stem import PorterStemmer 
def stemmize(tokens):
    ps = PorterStemmer()
    stemmedTokens = []
    for word in tokens:
        stemmedTokens.append(ps.stem(word))
    return stemmedTokens

def hashtagToWord(tokens):
    newTokens = []
    for token in tokens:
        newTokens.append(token.replace('#',''))
    return newTokens

# Lematization
from nltk.stem import WordNetLemmatizer
def lemmatize(tokens):
    lem = WordNetLemmatizer()
    lemmatizedTokens = []
    for word in tokens:
        lemmatizedTokens.append(lem.lemmatize(word))
    return lemmatizedTokens


# The FINAL Tokenizer
from nltk.tokenize import TweetTokenizer
from nltk.sentiment.util import mark_negation
def superTokenize(text, mark_neg, remSW, lem, stem):
    tokens = TweetTokenizer().tokenize(text)
    if mark_neg:    tokens = mark_negation(tokens)
    if remSW:       tokens = remStopWords(tokens)
    if lem:         tokens = lemmatize(tokens)
    if stem:        tokens = stemmize(tokens) 
    return tokens

from lexicons import getLexicons
def getEmotionLexicons():
    lexicons = getLexicons()
    emotions = ['anger','fear','joy','sadness']
    emotionLexicons = {}
    for emotion in emotions:
        emotionLexicons[emotion] = []
    for key in lexicons:
        for emotion in emotions:
            if lexicons[key][4] == ('#'+emotion):
                emotionLexicons[emotion].append(key)
    return emotionLexicons
emotionLexicons = getEmotionLexicons()

# Emojis
from emoji import UNICODE_EMOJI
def getEmojis():
    emojis = []
    for key in UNICODE_EMOJI:
        emojis.append(key)
    return emojis
emojis = getEmojis()
lex = getLexicons()

def tokenizeAnger(text):
    tokens = superTokenize(text, False, True, True, True)
    newTokens = []
    for token in tokens:
        if token in emotionLexicons['anger']:
            if float(lex[token][7])>-0.5:
                newTokens.append('LOW')
            elif float(lex[token][7])>-0.8:
                newTokens.append('MEDIUM')
            else:
                newTokens.append('HIGH')
            newTokens.append('ANGER')
        elif token in emojis:
            text_emoji = UNICODE_EMOJI[token]
            text_emoji.replace(':','')
            text_emoji.replace('_',' ')
            words = text_emoji.split()
            newTokens = newTokens+remStopWords(words)
        else:
            newTokens.append(token)
    return newTokens

def tokenizeFear(text):
    tokens = superTokenize(text, False, True, True, True)
    newTokens = []
    for token in tokens:
        if token in emotionLexicons['fear']:
            newTokens.append('FEAR')
        elif token in emojis:
            text_emoji = UNICODE_EMOJI[token]
            text_emoji.replace(':','')
            text_emoji.replace('_',' ')
            words = text_emoji.split()
            newTokens = newTokens+remStopWords(words)
        else:
            newTokens.append(token)
    return newTokens

def tokenizeJoy(text):
    tokens = superTokenize(text, True, True, False, True)  
    newTokens = []
    for token in tokens:
        if token in emotionLexicons['joy']:
            if float(lex[token][2])<0.5:
                newTokens.append('LOW')
            elif float(lex[token][2])<0.8:
                newTokens.append('MEDIUM')
            else:
                newTokens.append('HIGH')
            newTokens.append('JOY')
        else:
            newTokens.append(token)
    return newTokens

def tokenizeSadness(text):
    tokens = superTokenize(text, True, True, False, True)
    newTokens = []
    for token in tokens:
        if token in emotionLexicons['sadness']:
            newTokens.append('SAD')
        else:
            newTokens.append(token)
    return newTokens



"""
    Consejo para el vectorizador: investigar los modulos de nltk, en particular, 
    TweetTokenizer, mark_negation. También, el parámetro ngram_range para clasificadores 
    no bayesianos.

    Consejo para el clasificador: investigar otros clasificadores mas efectivos que naive
    bayes. Ojo q naive bayes no debería usarse con n-gramas, ya que rompe el supuesto de 
    independencia.
"""

# Clasifiers
from sklearn.linear_model import SGDClassifier, LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

def get_classifierAnger():
     # Inicializamos el Vectorizador para transformar las oraciones a BoW 
    vectorizer = CountVectorizer(tokenizer=tokenizeAnger, ngram_range=(1,2))
    # Clasificadores.
    lr = LogisticRegression()
    mlp = MLPClassifier() # mas auc
    svc = SVC(kernel='linear', probability=True) 

    text_clf = Pipeline([('vect', vectorizer), ('clf',svc)])
    return text_clf

def get_classifierFear():
        # Inicializamos el Vectorizador para transformar las oraciones a BoW 
    vectorizer = CountVectorizer(tokenizer=tokenizeFear, ngram_range=(1,2))

    # Clasificadores.
    mlp = MLPClassifier() # mas auc
    svc = SVC(kernel='linear', probability=True) 

    text_clf = Pipeline([('vect', vectorizer), ('clf', svc)])
    return text_clf

def get_classifierJoy():
        # Inicializamos el Vectorizador para transformar las oraciones a BoW 
    vectorizer = CountVectorizer(tokenizer=tokenizeJoy, ngram_range=(1,2))

    # Clasificadores.
    mlp = MLPClassifier() # mas auc
    svc = SVC(kernel='linear', probability=True)
  
    text_clf = Pipeline([('vect', vectorizer), ('clf', svc)])
    return text_clf


def get_classifierSadness():
    # Inicializamos el Vectorizador para transformar las oraciones a BoW 
    vectorizer = CountVectorizer(tokenizer=tokenizeSadness, ngram_range=(1,1))

    # Clasificadores.
    mlp = MLPClassifier() 
    svc = SVC(kernel='linear', probability=True) 
  
    text_clf = Pipeline([('vect', vectorizer), ('clf', svc)])
    return text_clf

from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer
def get_classifier():
    
    # Inicializamos el Vectorizador para transformar las oraciones a BoW 
    #angerTokenizer = superTokenize(mark_neg=True, remSW=True, lem=True, stem=True)

    vectorizer = CountVectorizer(tokenizer=superTokenizeAnger, ngram_range=(2,2))
    
    # Clasificadores.
    lr = LogisticRegression()
    mlp = MLPClassifier() 
    k_neighbors = KNeighborsClassifier(5)
    svc = SVC(kernel='linear', probability=True) 

    classifier = Pipeline([('vect', vectorizer), ('clf', svc)])
    return classifier


# Esto de aquí imprime los datos importantes
# Esta función imprime la matriz de confusión, 
# el reporte de clasificación y las metricas 
# usadas en la competencia:

def evaulate(predicted, y_test, labels, key):
    # Importante: al transformar los arreglos de probabilidad a clases,
    # entregar el arreglo de clases aprendido por el clasificador. 
    # (que comunmente, es distinto a ['low', 'medium', 'high'])
    predicted_labels = [labels[np.argmax(item)] for item in predicted]
    
    # Confusion Matrix
    print('Confusion Matrix for {}:\n'.format(key))

    # Classification Report
    print(
        confusion_matrix(y_test,
                         predicted_labels,
                         labels=['low', 'medium', 'high']))

    print('\nClassification Report')
    print(
        classification_report(y_test,
                              predicted_labels,
                              labels=['low', 'medium', 'high']))

    # AUC
    print("auc: ", auc(y_test, predicted))

    # Kappa
    print("kappa:", cohen_kappa_score(y_test, predicted_labels))

    # Accuracy
    print("accuracy:", accuracy_score(y_test, predicted_labels), "\n")

    print('------------------------------------------------------\n\n')


# Tengo tuto
# Clasifica un dataset. Retorna el modelo ya entrenado mas sus labels asociadas.

def classify(dataset, key):

    X_train, X_test, y_train, y_test = split_dataset(dataset)

    text_clf = get_classifier()

    # Entrenar el clasificador
    text_clf.fit(X_train, y_train)

    # Predecir las probabilidades de intensidad de cada elemento del set de prueba.
    predicted = text_clf.predict_proba(X_test)

    # Obtener las clases aprendidas.
    learned_labels = text_clf.classes_

    # Evaluar
    evaulate(predicted, y_test, learned_labels)
    return text_clf, learned_labels

def classifyAnger(dataset, key):

    X_train, X_test, y_train, y_test = split_dataset(dataset)

    text_clf = get_classifierAnger()

    # Entrenar el clasificador
    text_clf.fit(X_train, y_train)

    # Predecir las probabilidades de intensidad de cada elemento del set de prueba.
    predicted = text_clf.predict_proba(X_test)

    # Obtener las clases aprendidas.
    learned_labels = text_clf.classes_

    # Evaluar
    evaulate(predicted, y_test, learned_labels, key)
    return text_clf, learned_labels

def classifyFear(dataset, key):

    X_train, X_test, y_train, y_test = split_dataset(dataset)

    text_clf = get_classifierFear()

    # Entrenar el clasificador
    text_clf.fit(X_train, y_train)

    # Predecir las probabilidades de intensidad de cada elemento del set de prueba.
    predicted = text_clf.predict_proba(X_test)

    # Obtener las clases aprendidas.
    learned_labels = text_clf.classes_

    # Evaluar
    evaulate(predicted, y_test, learned_labels,key)
    return text_clf, learned_labels

def classifyJoy(dataset, key):

    X_train, X_test, y_train, y_test = split_dataset(dataset)

    text_clf = get_classifierJoy()

    # Entrenar el clasificador
    text_clf.fit(X_train, y_train)

    # Predecir las probabilidades de intensidad de cada elemento del set de prueba.
    predicted = text_clf.predict_proba(X_test)

    # Obtener las clases aprendidas.
    learned_labels = text_clf.classes_

    # Evaluar
    evaulate(predicted, y_test, learned_labels, key)
    return text_clf, learned_labels

def classifySadness(dataset, key):

    X_train, X_test, y_train, y_test = split_dataset(dataset)

    text_clf = get_classifierSadness()

    # Entrenar el clasificador
    text_clf.fit(X_train, y_train)

    # Predecir las probabilidades de intensidad de cada elemento del set de prueba.
    predicted = text_clf.predict_proba(X_test)

    # Obtener las clases aprendidas.
    learned_labels = text_clf.classes_

    # Evaluar
    evaulate(predicted, y_test, learned_labels, key)
    return text_clf, learned_labels



# Ejecutar el clasificador por cada dataset

classifiers = []
learned_labels_array = []

# Por cada llave en train ('anger', 'fear', 'joy', 'sadness')
#for key in train:
 #   classifier, learned_labels = classify(train[key], key)
  #  classifiers.append(classifier)
   # learned_labels_array.append(learned_labels)

classifierAnger, learned_labels_anger = classifyAnger(train['anger'], 'anger')
classifiers.append(classifierAnger)
learned_labels_array.append(learned_labels_anger)

classifierFear, learned_labels_fear = classifyAnger(train['fear'], 'fear')
classifiers.append(classifierFear)
learned_labels_array.append(learned_labels_fear)

classifierJoy, learned_labels_joy = classifyAnger(train['joy'], 'joy')
classifiers.append(classifierJoy)
learned_labels_array.append(learned_labels_joy)

classifierSadness, learned_labels_sadness = classifyAnger(train['sadness'], 'sadness')
classifiers.append(classifierSadness)
learned_labels_array.append(learned_labels_sadness)



# Predecir el Target set

def predict_target(dataset, classifier, labels):
    # Predecir las probabilidades de intensidad de cada elemento del target set.
    predicted = pd.DataFrame(classifier.predict_proba(dataset.tweet), columns=labels)
    # Agregar ids
    predicted['id'] = dataset.id.values
    # Reordenar
    predicted = predicted[['id', 'low', 'medium', 'high']]
    return predicted



# Predicción y guardado de archivos

predicted_target = {}

if (not os.path.isdir('./predictions')):
    os.mkdir('./predictions')

else:
    # Eliminar predicciones anteriores:
    shutil.rmtree('./predictions')
    os.mkdir('./predictions')

for idx, key in enumerate(target):
    # Predecir el target set
    predicted_target[key] = predict_target(target[key], classifiers[idx],
                                           learned_labels_array[idx])
    # Guardar predicciones
    predicted_target[key].to_csv('./predictions/{}-pred.txt'.format(key),
                                 sep='\t',
                                 header=False,
                                 index=False)

# Crear archivo zip
a = shutil.make_archive('predictions', 'zip', './predictions')