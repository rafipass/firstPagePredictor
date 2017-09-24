import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

import csv
import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, asin

from matplotlib import cm
from matplotlib import gridspec
from matplotlib import pyplot as plt

import sklearn.metrics as metrics
import tensorflow as tf
from tensorflow.contrib.learn.python.learn import learn_io

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix

from sklearn import metrics
from sklearn.cross_validation import KFold
from sklearn.preprocessing import StandardScaler

tf.logging.set_verbosity(tf.logging.ERROR)
pd.options.display.max_rows = 10
pd.options.display.float_format = '{:.1f}'.format
#####################
path_train = "doc2vec.csv"

path_scores="doc2vecIndex.csv"
threshold=50
print("Loading Train Data")
train = pd.read_csv(path_train, sep=",")
print train.count
train=train.iloc[:,:20]

scores=pd.read_csv(path_scores, sep=",")
print scores.count
print scores['score']
scores_list=scores['score']
targets=[]
for idx in xrange(len(scores_list)):
    if scores_list[idx]>threshold:
        targets.append(1)
    else:
        targets.append(0)
targets = pd.DataFrame(targets)
print targets


######################
def train_linear_classifier_model(
    learning_rate,
    steps,
    batch_size,
    training_examples,
    training_targets,
    validation_examples,
    validation_targets):
  """Trains a linear regression model of one feature.

  In addition to training, this function also prints training progress information,
  as well as a plot of the training and validation loss over time.

  Args:
    learning_rate: A `float`, the learning rate.
    steps: A non-zero `int`, the total number of training steps. A training step
      consists of a forward and backward pass using a single batch.
    batch_size: A non-zero `int`, the batch size.
    training_examples: A `DataFrame` containing one or more columns from
      `dataframe` to use as input features for training.
    training_targets: A `DataFrame` containing exactly one column from
      `dataframe` to use as target for training.
    validation_examples: A `DataFrame` containing one or more columns from
      `dataframe` to use as input features for validation.
    validation_targets: A `DataFrame` containing exactly one column from
      `dataframe` to use as target for validation.

  Returns:
    A `LinearClassifier` object trained on the training data.
  """

  periods = 10
  steps_per_period = steps / periods

  # Create a linear classifier object.
  feature_columns = set([tf.contrib.layers.real_valued_column(my_feature) for my_feature in training_examples])
  linear_classifier = tf.contrib.learn.LinearClassifier(
      feature_columns=feature_columns,
      optimizer=tf.train.GradientDescentOptimizer(learning_rate=learning_rate));


  # Create input functions
  training_input_fn = learn_io.pandas_input_fn(
     x=training_examples, y=training_targets,
     num_epochs=None, batch_size=batch_size)

  predict_training_input_fn = learn_io.pandas_input_fn(
     x=training_examples, y=training_targets,
     num_epochs=1, shuffle=False)

  predict_validation_input_fn = learn_io.pandas_input_fn(
      x=validation_examples, y=validation_targets,
      num_epochs=1, shuffle=False)

  # Train the model, but do so inside a loop so that we can periodically assess
  # loss metrics.
  print "Training model..."
  print "Log loss (on training data):"
  training_errors = []
  validation_errors = []
  for period in range (0, periods):
    # Train the model, starting from the prior state.
    linear_classifier.fit(
        input_fn=training_input_fn,
        steps=steps_per_period
        )

    # Take a break and compute predictions.
    training_probabilities = np.array(list(linear_classifier.predict_proba(input_fn=predict_training_input_fn)))
    validation_probabilities = np.array(list(linear_classifier.predict_proba(input_fn=predict_validation_input_fn)))
    # Compute training and validation loss.
    training_log_loss = metrics.log_loss(training_targets, training_probabilities[:,1])
    validation_log_loss = metrics.log_loss(validation_targets, validation_probabilities[:,1])
    training_roc = metrics.roc_auc_score(training_targets, training_probabilities[:, 1])
    validation_roc = metrics.roc_auc_score(validation_targets, validation_probabilities[:, 1])
    # Occasionally print the current loss.
    print "  period %02d : %0.2f" % (period, training_log_loss)
    # Add the loss metrics from this period to our list.
    training_errors.append(training_log_loss)
    validation_errors.append(validation_log_loss)
  print "Model training finished."

  # Output a graph of loss metrics over periods.
  plt.ylabel("LogLoss")
  plt.xlabel("Periods")
  plt.title("LogLoss vs. Periods")
  plt.tight_layout()
  plt.plot(training_errors, label="training")
  plt.plot(validation_errors, label="validation")
  plt.legend()

  return linear_classifier
#####################

print("Validation...")

nb_folds = 4
kfolds = KFold(len(targets), nb_folds, shuffle=True, random_state=1337)
av_roc = 0.
f = 0

print kfolds


#    To train the logistic regression classifier with features and target data
#    :param features:
#    :param target:
#    :return: trained  classifier

for trainrows, validrows in kfolds:
    print('---'*20)
    print('Fold', f)
    print('---'*20)
    f += 1
    train_rows = train.iloc[trainrows,:]
    train_validation = train.iloc[validrows,:]
    labels_train = targets.iloc[trainrows]
    labels_validation = targets.iloc[validrows]

    linear_classifier = train_linear_classifier_model(
    learning_rate=0.05,
    steps=500,
    batch_size=20,
    training_examples=train_rows,
    training_targets=labels_train,
    validation_examples=train_validation,
    validation_targets=labels_validation)
