from inspect import signature, isgeneratorfunction

from qcodes import StandardParameter


def pass_operator(point_functions):
    def inner(station, namespace):
        for value in point_functions[0](station, namespace):
            yield (value, )

    return inner


def _product_two_operator(pf1, pf2):

    def tpl(value):
        if not isinstance(value, tuple):
            return value,
        return value

    def inner(station, namespace):
        for v1 in pf1(station, namespace):
            for v2 in pf2(station, namespace):
                yield tpl(v2) + tpl(v1)  # This is not a bug, the addition here is in the right order

    return inner


def product_operator(point_functions):

    def inner(station, namespace):
        rval = point_functions[0]
        for pf in point_functions[1:]:
            rval = _product_two_operator(pf, rval)

        return rval(station, namespace)

    return inner


class BaseSweepObject:
    def __init__(self, parameters, point_functions, chain_operator):
        """
        Parameters
        ----------
        parameters: list, qcodes.StandardParameter
        point_functions: list, generator_function, n_parameters
            A list of equal length as the number of parameters. Each generator function accepts two parameters; a
             QCoDeS Station and a pysweep Namespace. Each "next" operation on the generators gives the next value to be
             set on the parameters
        chain_operator: callable
            Callable which accepts a list of generator functions as input and returns a single generator function. This
            function accepts two parameters: a QCoDeS Station and a pysweep Namespace
        """

        self._parameters = parameters
        self._point_functions = point_functions
        self._chain_operator = chain_operator

        self._point_generator = None
        self._station = None
        self._namespace = None

    def __next__(self):
        values = next(self._point_generator)
        return {p.label: {"unit": p.units, "value": v} for p, v in zip(self._parameters, values)}

    def __iter__(self):
        self._point_generator = self._chain_operator(self._point_functions)(self._station, self._namespace)
        return self

    def set_station(self, station):
        self._station = station

    def set_namespace(self, namespace):
        self._namespace = namespace

    def unset_namespace(self):
        self._namespace = None


class SweepObject(BaseSweepObject):
    def __init__(self, parameter, point_function):
        """
        Parameters
        ----------
        parameter: list, qcodes.StandardParameter
        point_function: iterable or a function returning an iterable
        """
        if not isinstance(parameter, StandardParameter):
            raise ValueError("The Parameter should be of type QCoDeS StandardParameter")

        self.parameter = parameter
        if not callable(point_function):
            self.point_function = lambda station, namespace: (i for i in point_function)
        else:
            self.point_function = point_function

        super().__init__([self.parameter], [self.point_function], chain_operator=pass_operator)


def sweep_product(sweep_objects):
    """
    Parameters
    ----------
    sweep_objects: list, SweepObject
    """

    params = [so.parameter for so in sweep_objects]
    point_functions = [so.point_function for so in sweep_objects]

    return BaseSweepObject(params, point_functions, chain_operator=product_operator)

