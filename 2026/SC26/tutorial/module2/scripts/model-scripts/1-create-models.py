#!/usr/bin/env python3

# This can be run from inside a client (or the lammps container)
# that has river and the client installed.

import sys

from river import linear_model, preprocessing
from riverapi.main import Client

url = "http://localhost"
if len(sys.argv) > 1:
    url = sys.argv[1]

print(f"Preparing to create models for client URL {url}")

# Connect to the server running here
cli = Client(url)

# Upload several models to test for lammps - these are different kinds of regressions
regression_model = preprocessing.StandardScaler() | linear_model.LinearRegression(
    intercept_lr=0.1
)

# That's kind of cool, although I'm not sure I like PA people, not sure how I feel about ML models :)
# https://www.geeksforgeeks.org/passive-aggressive-classifiers/
pa_regression = model = linear_model.PARegressor(
    C=0.01, mode=2, eps=0.1, learn_intercept=False
)

# https://riverml.xyz/latest/api/linear-model/BayesianLinearRegression/
bayesian_regression = linear_model.BayesianLinearRegression()

for model in [regression_model, bayesian_regression, pa_regression]:
    model_name = cli.upload_model(model, "regression")
    print("Created model %s" % model_name)
