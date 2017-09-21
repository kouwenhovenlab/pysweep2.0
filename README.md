# PySweep 2.0 interface and design decisions
## Introduction
PySweep is a framework intended to be used on top of qcodes [QCoDeS](https://github.com/QCoDeS/Qcodes) in order to define measurements flexibly. At the most general level, a measurement has dependent and independant variables with setup and clean up methods. These need to be specified somehow. We intend the following structure:  

```python 
 measurement_table = {
  "independent_variables": {
    "gate1": {
      "unit": "V",
      "set_function": some.instrument.set, 
      "values": iterable_values
     }
     "gate2": {
        "unit": "V",
        "set_function": other.instrument.set, 
        "values": generator_values
     }
  },
  "dependent_variables": {
    "source_drain": {
    "unit": "A", 
    "get_function": yet_another.instrument.get
    }
  }
}
```

In the above example we have defined two independent variables. Our measurement loop therefore will be a nested loop where the first independent variable will be located in the inner most loop and will be the one which is sweeping most frequently.  

We can also couple to independent variables together to get a "co-sweep" like so: 

```python
"gate1, gate2" : {
 "unit": "V, V"
 "set_function": (some.instrument.set, other.instrument.set),
 "values": (iterable_values1, iterable_values2)
}
```

The measurement table will also ensure the proper formatting and labeling of the resulting measurement file. We note that the "values" field of indepenent variables can be iterators or generators. This will allow us to introduce considerable flexibility (for example, introduce feedback and adaptive stepping in calibration measurements). 

## Measurement setup and cleanup 

The measurement 