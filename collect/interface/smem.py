import re
import subprocess


def collect_memorydata(time: int, frequency: int, mode="name", number=5):
    """

    :param time:
        The number of seconds for which to collect data.
    :param frequency:
        The frequency in Hz with which to sample the data.
    :param mode:
        "name" or "pid" or "command", to decide the labelling
    :param number:
        The number of processes to find

    :return:
        An iterator of :class: `DataPoint` objects.

    """
    ticks = time * frequency
    datapoints = {}

    for tick in range(ticks):
        _time = tick/frequency
        if mode == "name":
            out = subprocess.getoutput("smem -c \"name pss\" | tac")
        elif mode == "command":
            out = subprocess.getoutput("smem -c \"command pss\" | tac")
        else:
            raise ValueError("mode {} not supported.".format(mode))

        datapoints[_time] = {}

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

            if label in datapoints[_time]:
                memory += int(datapoints[_time][label])
            else:
                index += 1
                if index >= number:
                    if "other" not in datapoints[_time]:
                        datapoints[_time]["other"] = 0

                    datapoints[_time]["other"] = datapoints[_time]["other"] +\
                                                 memory
                    continue

            datapoints[_time][label] = memory

        for lab in datapoints[_time]:
            mem = datapoints[_time][lab]
            print("{},{},{}".format(_time, mem, lab))


if __name__ == "__main__":
    collect_memorydata(10, 1, "name", 5)
