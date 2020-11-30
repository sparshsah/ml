"""
Arbitrary-depth, arbitrary-width feedforward artificial neural network.
Step-by-step Python implementation of simple deep learning for binary classification.
Source code in `fann.py`, demo in `fann.ipynb`.
"""

# data structures
import pandas as pd
# algorithms
import numpy as np


########################################################################################################################
# WEIGHTS DATA STRUCTURE ###############################################################################################
########################################################################################################################

"""
An ANN is essentially identified by its forward-propagation weights. We store the model as a pd.DataFrame.
Each row (on the index, AKA the 0th axis) represents a layer. The first column is always reserved for the bias term.
Note that because different layers can have different widths, some rows may not be completely filled across.
"""


########################################################################################################################
# ACTIVATION FUNCTION ##################################################################################################
########################################################################################################################

"""
Three common neuron activation functions are logistic (AKA sigmoid), tanh, and ReLU.
We like the logistic for (binary) classification tasks, for the slightly (maybe even misleadingly) arbitrary reason
that its output lies in [0, 1], so it can be interpreted as this neuron's "best guess"
of the probability that the input belongs to Category 1. As further support, the logistic's generalization, the softmax,
is a commonly-used "output squashing" function for multinomial classification tasks: It transforms a `n`-vector
of Real numbers into a probability mass distribution. (And tanh is simply a scaled-and-shifted version of logistic.)
ReLU is cool too, and has another cool connection, this time to the hinge loss function.
"""


########################################################################################################################
# LOSS FUNCTION ########################################################################################################
########################################################################################################################

def get_ll(p: pd.Series) -> float:
    """
    Log likelihood of a series of independent outcomes.
    More numerically stable than raw likelihood.

    input
    -----
    p: pd.Series, the probability of each outcome.

    output
    ------
    float, the joint log likelihood of the outcomes.
    """
    return np.log(p).sum()


def _get_loss(p_y: pd.Series) -> float:
    """
    Negative log likelihood loss.

    input
    -----
    p_y: pd.Series, how much probability mass we assigned to the correct label for each point.
        E.g. if p_y = [0.10, 0.85, 0.50], then there were 2 data points. For the first point,
        we distributed 1-0.10=0.90 probability mass among incorrect labels. Depending on
        how many categories there are, this is pretty poor. In particular, if this is a
        binary classification task, then a simple coin flip would distribute only 0.50
        probability mass to the incorrect label (whichever that might be).
        For the second point, we distributed only 1-0.85=0.15 probability mass
        among incorrect labels. This is pretty good. For the last point,
        we distributed exactly half the probability mass among incorrect labels.

    output
    ------
    float, the calculated loss.
    """
    return -get_ll(p=p_y)


def get_loss(p_hat: pd.DataFrame, y: pd.Series) -> float:
    """
    Negative log likelihood loss.

    input
    -----
    p_hat: pd.DataFrame (columns = category labels, index = observations),
        how much probability mass we assigned to each category label for each point.
        Each row should be a well-formed probability mass function
        AKA discrete probability distribution.

    y: pd.Series, the correct category label for each point.

    output
    ------
    float, the calculated loss.
    """
    # pick out the entry for the correct label in each row
    p_y = pd.Series({n: p_hat.loc[n, label] for n, label in y.items()})
    return _get_loss(p_y=p_y)
