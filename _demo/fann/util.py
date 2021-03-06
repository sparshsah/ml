"""
Helper packages and functions we'll use in our demo.

They mainly just wrangle data into the various formats
expected by us, `sklearn`, `matplotlib`, etc.

Not necessarily the most elegant API or implementation.
It's not important to read every single line of every single one.
"""

# target source code
import foggy_ml.util as util  # assumes `/path/to/foggy-ml` in `PYTHONPATH`, so pylint: disable=import-error
import foggy_ml.fann as fann  # again, pylint: disable=import-error

# syntax utils
from typing import Tuple, List, Dict, Callable, Union, Optional
from importlib import reload
# data loading
import sklearn.datasets as datasets
# data structures
import pandas as pd
# data wrangling
from sklearn.preprocessing import StandardScaler as FeatureScaler
# calculations and algorithms
import numpy as np
from sklearn.neural_network import MLPClassifier as RefNN  # reference implementation
# visualization
import matplotlib.pyplot as plt

RADIANS_PER_CIRCLE: float = 2 * np.pi
CIRCLE_SCALE: float = 4
NUM_FEATURES: int = 2  # aka num of neurons on input layer
NUM_CATEGORIES: int = 2  # aka num of neurons on output layer
LAYER_WIDTH: Tuple[int] = (4, 3)  # first hidden layer has 4 neurons, second hidden layer has 3 neurons


def get_unit_circle(k: int=NUM_CATEGORIES, scale: float=CIRCLE_SCALE) -> List[Tuple[float, float]]:
    """Uniformly sample `k` points on the unit circle in the 2D plane."""
    a = RADIANS_PER_CIRCLE / k
    return [( np.cos(a*l)*scale , np.sin(a*l)*scale ) for l in range(k)]


def lrange(*args) -> list:
    return list(range(*args))


def titlefy(d: str) -> str:
    """E.g. 'train' -> 'TRAINING DATA'."""
    return f"{d}ing Data".upper()


def _gen_data(num_categories: int=NUM_CATEGORIES, n: int=256, noise: float=0.32, random_seed: int=1337,
              x_scaler: Optional[FeatureScaler]=None) ->\
        Tuple[Dict[str, Union[pd.DataFrame, pd.Series]], FeatureScaler]:
    if num_categories == NUM_CATEGORIES:
        X, y = datasets.make_moons(n_samples=n, noise=noise, random_state=random_seed)
    else:
        X, y = datasets.make_blobs(centers=get_unit_circle(k=num_categories), n_samples=n,
                                   random_state=random_seed)
    assert X.shape[1] == NUM_FEATURES, (len(X), NUM_FEATURES)
    assert len(set(y)) == num_categories, (len(set(y)), num_categories)
    x_scaler = FeatureScaler().fit(X) if x_scaler is None else x_scaler
    X = x_scaler.transform(X)
    X = pd.DataFrame(X)
    y = pd.Series(y)
    data = {"X": X, "y": y}
    return data, x_scaler


def gen_data(num_categories: int=NUM_CATEGORIES):
    data = {}
    data["train"], x_scaler = _gen_data(num_categories=num_categories)
    # for simplicity, we pretend we know ground-truth optimal hyperparameters -> don't need tuning data
    # data["Tuning Data"], _ = gen_data(num_categories=num_categories, random_seed=1337+1, x_scaler=x_scaler)
    data["test"], _ = _gen_data(num_categories=num_categories, random_seed=1337+2, x_scaler=x_scaler)
    return data


def homebrewify(ref_nn: RefNN, layer_width: Tuple[float]=LAYER_WIDTH) -> fann.NN:
    """Reformat reference implementation weights data structure as homebrew."""
    # hidden layers
    hidden_layers = []
    # init: in 1st iteration, each neuron on input layer will get weighted & fed into each neuron on 1st hidden layer
    prev_neuron_indices = lrange(NUM_FEATURES)
    for l, width in enumerate(layer_width):
        curr_neuron_indices = lrange(width)
        del width
        layer = fann.Layer(index=curr_neuron_indices, columns=[fann.BIAS_INDEX] + prev_neuron_indices)
        # populate bias weights
        layer.loc[:, fann.BIAS_INDEX] = ref_nn.intercepts_[l]
        # populate non-bias weights
        layer.loc[:, prev_neuron_indices] = ref_nn.coefs_[l].T
        del l
        hidden_layers.append(layer.astype(float))
        del layer
        # in next iteration, each neuron on this layer will get weighted & fed into each neuron on next layer
        prev_neuron_indices = curr_neuron_indices
        del curr_neuron_indices
    del layer_width

    # output layer
    """
    We use 2 output neurons & predict category label
    (0 or 1) based on whose activation is stronger..
    sklearn uses single output neuron & predicts category label
    (0 or 1) based on whether its activation < or >= 0.50.

    Therefore, in replicating sklearn's model, we make
    our zeroth output neuron a dummy whose
    (both bias & non-bias) weights are the negative of
    our first output neuron's  weights, which are exactly equal
    to sklearn's single output neuron's weights.
    With this setup, our first output neuron's outgoing activation
    will always exactly match sklearn's single output neuron's
    outgoing activation i.e. the estimated probability that
    the current data point belongs to category 1.

    And what about our zeroth output neuron's outgoing activation?
    We can write a neuron's activation function input as
    `x = b + w'a` where `b` is its bias, `w` is its weight vector,
    and `a` is the previous layer's output.
    And a property of the logistic function is that f(-x) = 1 - f(x).
    Hence, our zeroth output neuron's outgoing activation will be
    f(-b - w'a) = f(-(b + w'a)) = 1 - f(b + w'a) i.e.
    the complement probability of our first output neuron's
    outgoing activation i.e. the estimated probability that
    the current data point belongs to category 0.

    Thus, thanks to our careful bookkeeping, before we squash,
    our output probabilities will exactly match sklearn's.
    This conveniently helps us replicate sklearn's predictions.

    The obvious wrinkle is that we then squash this,
    which isn't an identity transformation here: for example,
    if our pre-squash output is [0, 1] i.e. 100% probability
    that the current data point belongs to category 1, our post-squash
    output will be [0.27, 0.73]. This is different from sklearn which
    for binary classification tasks does /not/ squash its output.
    (If you read sklearn's multi-layer perceptron source code, you'll see
    they use `if-else` statements to implement special handling
    for binary classification tasks.)

    However, the important thing is that we preserve the
    relative magnitude of each entry, which will
    always be the case since `exp()` is a strictly increasing function.
    As long as this holds, we still ultimately will select the same
    predicted category as sklearn.

    So, why is this important to our model construction?
    Well, using the single row index `-1` for ref model
    would apply even to multinomial classification,
    since it simply extracts ref model's final i.e. output layer.
        But, using the single index (column `0` for ref model,
    and row `0` or `1` for homebrew model)
    is the part that assumes this is binary classification,
    since it assumes there are only 2 categories in the output layer.
    """
    if NUM_CATEGORIES != 2:
        raise ValueError(f"Got K={NUM_CATEGORIES} categories, but assume binary i.e. K=2 classification!")
    output_layer = fann.Layer(index=range(NUM_CATEGORIES), columns=[fann.BIAS_INDEX] + prev_neuron_indices)
    # populate bias weights
    output_layer.loc[0, fann.BIAS_INDEX] = -ref_nn.intercepts_[-1][0]
    output_layer.loc[1, fann.BIAS_INDEX] = ref_nn.intercepts_[-1][0]
    # populate non-bias weights
    output_layer.loc[0, prev_neuron_indices] = -ref_nn.coefs_[-1].T[0]
    output_layer.loc[1, prev_neuron_indices] = ref_nn.coefs_[-1].T[0]
    del prev_neuron_indices

    return fann.nnify(nn=hidden_layers + [output_layer.astype(float)])


def plot_data(X: pd.DataFrame, y: pd.Series, title: Optional[str]=None,
              ax: Optional[plt.matplotlib.axes._base._AxesBase]=None):
    ax = plt if ax is None else ax
    # caution: in scatterplot, `x` is actually X[0] i.e. the 1st feature, `y` is X[1] i.e. 2nd feature
    ax.scatter(x=X[0], y=X[1], c=y/y.max(), cmap=plt.cm.get_cmap("coolwarm"))
    try:
        ax.set_title(title)
    except AttributeError:
        # if e.g. ax == plt
        ax.title(title)
    if ax == plt:
        ax.show()


def plot_datas(X0: pd.DataFrame, y0: pd.Series, X1: pd.DataFrame, y1: pd.Series,
               title0: Optional[str]=None, title1: Optional[str]=None, suptitle: Optional[str]=None):
    _, axs = plt.subplots(ncols=2, sharex=True, sharey=True, figsize=(8, 4))
    plot_data(X=X0, y=y0, title=title0, ax=axs[0])
    plot_data(X=X1, y=y1, title=title1, ax=axs[1])
    if suptitle is not None:
        plt.suptitle(suptitle)
    plt.show()


def plot_perf(X: pd.DataFrame, y: pd.Series, y_hat: pd.Series, suptitle: Optional[str]=None):
    score = np.mean(y_hat == y)
    plot_datas(X0=X, y0=y, title0="Ground Truth",
               X1=X, y1=y_hat, title1=f"Model (score = {score * 100: .2f}%)",
               suptitle=suptitle)


def plot_perfs(data: Dict[str, Union[pd.DataFrame, pd.Series]], pred_fn: Callable[[pd.DataFrame], pd.Series]):
    for d in "train", "test":
        plot_perf(X=data[d]["X"], y=data[d]["y"], y_hat=pred_fn(data[d]["X"]), suptitle=titlefy(d=d))
