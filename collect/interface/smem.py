import re
import subprocess
import time

from collect.interface.collecter import Collecter
from common import datatypes


# class MemoryGraph(Collecter):


def collect_memory_data(time_in_seconds: int, mode="name", number=5):
    """

    :param time_in_seconds:
        The number of seconds for which to collect data.
    :param mode:
        "name" or "pid" or "command", to decide the labelling
    :param number:
        The number of processes to find

    :return:
        An iterator of :class: `DataPoint` objects.

    """

    # Dict for the datapoints to be collected
    datapoints = {}
    
    # Set to collect all labels that have been encountered
    labels = set()

    # Set the start time
    start_time = time.monotonic()
    current_time = 0.0

    while current_time < time_in_seconds:
        if mode == "name":
            out = subprocess.getoutput("smem -c \"name pss\" | tac")
        elif mode == "command":
            out = subprocess.getoutput("smem -c \"command pss\" | tac")
        else:
            raise ValueError("mode {} not supported.".format(mode))

        datapoints[current_time] = {}

        index = 0
        for line in out.split("\n"):
            if re.match("Name", line) is not None:
                break

            match = re.match(r"\s*(?P<label>\S+(\s\S+)*)\s*"
                             r"(?P<memory>\d+)", line)
            if match is None:
                raise IOError("Invalid output format from smem: {}".format(
                    line))

            label = match.group("label")
            memory = int(match.group("memory"))

            if label in datapoints[current_time]:
                memory += int(datapoints[current_time][label])
            else:
                index += 1

                if index >= number:
                    if "other" not in datapoints[current_time]:
                        datapoints[current_time]["other"] = 0

                    datapoints[current_time]["other"] = \
                        float(int(datapoints[current_time]["other"] +
                                  memory/1024))
                    continue

                labels.add(label)

            datapoints[current_time][label] = float(int(memory/1024))
            
        # Update the clock
        current_time = time.monotonic() - start_time

    for key in datapoints:
        labels_at_key = set(list(datapoints[key].keys()))
        if labels_at_key != labels:
            for _label in labels - labels_at_key:
                datapoints[key][_label] = 0
            for lab in datapoints[key]:
                mem = datapoints[key][lab]
                yield datatypes.Datapoint(key, mem, lab)

# def _insert_datapoint(self, time, label, memory):
    # self.datapoints[time][label] = float(int(memory/1024))


if __name__ == "__main__":
    for data in collect_memory_data(5, "name", 10):
        print(data)
