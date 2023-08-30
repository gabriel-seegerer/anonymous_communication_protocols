import pickle
import csv
from matplotlib import pyplot as plt


def plot_graph(name, save=False):
    with open(f"timing_logs/{name}_pickle.pickle", "rb") as f:
        num_dict = pickle.load(f)

    x_values = num_dict.get("scale")
    y_values_min = num_dict.get("results_min")
    y_values_mean = num_dict.get("results_mean")

    if save:
        with open(f"timing_logs/saves/{name}_save.csv", "a", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(list(x_values) + [float("{:.2f}".format(v)) for v in y_values_min])

    plt.title(f"{num_dict.get('protocol')} Protocol - {num_dict.get('participants')} Participants - "
              f"{num_dict.get('datapoints')} Datapoints")
    plt.plot(x_values, y_values_min, color="green", label=num_dict.get('protocol'))
    # plt.plot(x_values, y_values_mean, color="red", label="mean")
    # plt.xscale("log")
    plt.grid(True)
    plt.xlabel("Number of participants")
    plt.ylabel("Latency [s]")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    plot_graph("fixed_role", save=True)
