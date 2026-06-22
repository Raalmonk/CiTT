# LLM Baseline Prompt: Benchmark 02 TEVC Equilibrium

You are given a simplified two-electrode voltage clamp equivalent circuit.

The circuit has:
- command voltage `Vc`,
- ideal buffer,
- finite-gain differential amplifier with gain `A = 100`,
- membrane resistance `Rm = 10 ohm`,
- output/electrode resistance `Ro = 10 ohm`,
- voltage electrode resistance `Re`,
- requested output membrane voltage `Vm`.

At equilibrium, ignore membrane capacitance and ion-channel dynamics. Treat omitted biological dynamics as assumptions, not blockers.

Tasks:
1. Explain the feedback loop.
2. Derive or describe how `Vm` is driven toward `Vc`.
3. Explain how finite amplifier gain affects tracking error.
4. Explain how electrode resistance `Re` affects the feedback measurement.
5. Identify where to probe `Vm`, amplifier output voltage, and clamp current.
6. State what information is missing for a numeric simulation.

Do not invent numeric values for `Vc` or `Re`. If numeric simulation is not possible, say why.
