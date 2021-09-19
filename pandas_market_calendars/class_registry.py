import pandas as pd


def _regmeta_class_factory(cls, name):
    """
    :param cls(RegisteryMeta): registration meta class
    :param name(str): name of class
    :return: class
    """
    if name in cls._regmeta_class_registry:
        return cls._regmeta_class_registry[name]
    else:
        raise RuntimeError(
            'Class {} is not one of the registered classes: {}'.format(name, cls._regmeta_class_registry.keys()))


def _regmeta_instance_factory(cls, name, *args, **kwargs):
    """
    :param cls(RegisteryMeta): registration meta class
    :param name(str): name of class that needs to be instantiated
    :param args(Optional(tuple)): instance positional arguments
    :param kwargs(Optional(dict)): instance named arguments
    :return: class instance
    """
    return cls._regmeta_class_factory(name)(*args, **kwargs)


def _regmeta_register_class(cls, regcls, name):
    """
    :param cls(RegisteryMeta): registration base class
    :param regcls(class): class to be registered
    :param name(str): name of the class to be registered
    """
    if hasattr(regcls, 'aliases'):
        if regcls.aliases:
            for alias in regcls.aliases:
                cls._regmeta_class_registry[alias] = regcls
        else:
            cls._regmeta_class_registry[name] = regcls
    else:
        cls._regmeta_class_registry[name] = regcls


def _regmeta_classes(cls):
    return list(cls._regmeta_class_registry.keys())


class RegisteryMeta(type):
    """
    Metaclass used to register all classes inheriting from RegisteryMeta
    """

    def __new__(mcs, name, bases, attr):
        cls = super(RegisteryMeta, mcs).__new__(mcs, name, bases, attr)

        if not hasattr(cls, '_regmeta_class_registry'):
            cls._regmeta_class_registry = {}
            cls._regmeta_class_factory = classmethod(_regmeta_class_factory)
            cls._regmeta_instance_factory = classmethod(_regmeta_instance_factory)
            cls._regmeta_classes = classmethod(_regmeta_classes)

        return cls

    def __init__(cls, name, bases, attr):
        _regmeta_register_class(cls, cls, name)
        for b in bases:
            if hasattr(b, '_regmeta_class_registry'):
                _regmeta_register_class(b, cls, name)
        super(RegisteryMeta, cls).__init__(name, bases, attr)

        # create a dictionary with a list of all cutoffs sorted descending for each market_time
        # for easy adjusting of datetimes according to historical variation
        cls._all_cut_offs = {}
        for market_time, times in cls._all_market_times.items():
            lst = list(times.keys())
            try: lst.remove(None)
            except ValueError:
                raise NotImplementedError("When setting market_times, exactly one entry should have None as key "
                                          "to represent the current/default time.")

            cls._all_cut_offs[market_time] = sorted(lst, reverse= True)

            # create the property for the market time, to be able to include special cases
            if market_time in ("market_open", "market_close"):
                _prop = market_time.replace("market_", "") + "s"

                old = "special_" + _prop
                prop = "special_" + market_time
                setattr(cls, prop, getattr(cls, old))
                setattr(cls, prop + "_adhoc", getattr(cls, old + "_adhoc"))

            else:
                prop = "special_" + market_time
                if not hasattr(cls, prop): setattr(cls, prop, _special_times_placeholder)
                prop += "_adhoc"
                if not hasattr(cls, prop): setattr(cls, prop, _special_times_placeholder)

        # create a list of market_times e.g.: ["market_open", "market_close"] for easy selection in .schedule
        cls._sorted_market_times = sorted(cls._all_market_times.keys(),
                                          key= lambda x: cls._all_market_times[x][None])


@property
def _special_times_placeholder(self): return []

