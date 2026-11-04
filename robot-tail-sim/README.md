# Tail support for a humanoid: simulation study

Question: can a human-size biped (1.75 m, 70 kg) use slower, cheaper leg servos
if it carries a tail that rests on the ground like a kangaroo's?

The full write-up with charts and video is the published report (link in the
session). This folder has the code and raw results.

## What is modelled

- `model.py`: MJCF builder. Segment lengths and masses follow Winter's
  anthropometric tables. Each leg has 5 actuated joints: hip roll, hip pitch,
  knee, ankle pitch, ankle roll. Trunk, head and arms form one rigid body.
  - **Tail** (optional): 5 hinges in the sagittal plane, each able to curl
    (0 to 1 rad) with a hard stop at straight.
    - Curl springs: 15 N·m/rad each.
    - One cable pulled by a winch straightens the tail. The winch is a
      series-elastic position actuator (400 kN/m, ≤ 4 kN, 0.1 m/s). The cable
      moment arm tapers from 10 cm at the root to 3 cm at the tip.
    - Tip: one wheel (`narrow`) or two wheels on a 44 cm axle (`wide`). The
      wheels roll freely forward and resist sideways slip.
    - Added mass, winch included: 3.8 kg.
- `sim.py`: servo model, controller and runner.
  - **Servo model.** Each servo has an internal PD position loop and a
    first-order torque lag. Torque follows a DC-motor torque-speed envelope
    (no motoring torque above no-load speed) on top of 0.12 kg·m² reflected
    rotor inertia. Latency is the sensor → controller → servo command loop.
    The controller runs at 500 Hz and physics at 1 kHz.
  - **Gait.** LIPM ZMP preview control (Kajita) plans the walk. Damped
    least-squares whole-body IK converts it to joint angles, solved online
    from delayed state. A capture-point stabilizer shifts the commanded COM.
    There is no step adjustment.
  - **Tail-specific parts.** The ZMP reference may sit in the hull of the feet
    plus the tail wheels: it stays 10–15 cm behind the stance ankle and moves
    continuously. A slow winch loop (τ = 0.3 s) holds the tail's share of body
    weight.
- `experiments.py`, `sweeps.py`, `extra.py`: batch runs (multiprocessing).
- `analyze.py`: summary tables and an actuator pick from a small price list.
- `render.py`, `make_videos.py`: offscreen rendering (OSMesa) to MP4.
- `report/`: HTML report template and builder.

## Run

```bash
pip install mujoco scipy matplotlib pillow
python3 sweeps.py          # ~15 min on 4 cores -> results/sweeps.json
python3 extra.py           # passive ankle roll, budget servos, faster gait -> results/extra.json
python3 analyze.py         # prints tables, writes results/summary.json
MUJOCO_GL=osmesa python3 make_videos.py 0.04
```

## Results

See `RESULTS.md` (generated alongside the report).
