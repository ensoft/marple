import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt


def show(csv):
    df = pd.read_csv(io.StringIO(csv.strip()))
    c = np.unique(df.C)
    labels = ['{}'.format(_c) for _c in c]
    args = [df[df.C == _c].B for _c in c]
    plt.stackplot(np.unique(df.A), args, labels=labels)
    plt.xlabel('A')
    plt.ylabel('C')
    plt.legend(loc='upper left')
    plt.show()
