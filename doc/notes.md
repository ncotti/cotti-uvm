# Analysis ports

Analysis ports are meant for the `check_phase()`. Data is fed
to them on the `run_phase()`, but, as their name implies, are just for analysis.

They are single writer, multiple subscribers.

Note: port is the one who generates the data, and export is the one who reads that data.

Analysis ports are created by `uvm_component`, specifically `Monitor`.

## Analysis port

Create it in your monitor's build phase

And connect it in the environment to the several subsscribers.

## Subscriber

If the component only subscribes to a single analysis port, then it can
inherit from `uvm_subscriber`.

An `uvm_subscriber` has an associated `self.analysis_export` that can be
connected to the analysis port.

The only requirement is to define the `def write(self, value)` method, which
is called every time a value is published in the analysis port.

You may then use those values later on the `check_phase()` or `report_phase()`.

## TLM analysis FIFOs

If your `uvm_component` needs to subscribe to more than one analysis port, you
need to create `uvm_tlm_analysis_fifo`s.

