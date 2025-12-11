# API documentation

This is the API documentation.

## End-user documentation

As an end user, we suggest to start with the main object in CoFMPy: the
[Coordinator](./coordinator.md). After creating your JSON configuration file, the
_Coordinator_ is the only CoFMPy object to start with: you can load the configuration
file, run a co-simulation and plot results.

## Developer documentation

As a developer, you may need to implement your own blocks, e.g. a custom data stream
handler. In this case, you must follow the same interface as the objects already
provided in CoFMPy: inheritance, abstract methods and members, etc. For more details,
take a look at the API documentation and the advanced user guide.
