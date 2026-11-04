"""Side-by-side videos: same servos, same pushes, biped vs tail."""
import os, sys
from render import side_by_side

STD_PUSH = [(2.6, 0.2, [60, 0, 0]), (4.2, 0.2, [0, 50, 0])]
os.makedirs("results", exist_ok=True)

lat = float(sys.argv[1]) if len(sys.argv) > 1 else 0.04
tag = int(round(lat * 1000))
side_by_side([
    (f"A: biped, servo latency {tag} ms", "A_biped",
     dict(gait=dict(t_start=4.5), simkw=dict(stab_k=0.5), servo=dict(latency=lat), push=STD_PUSH, T=13.0)),
    (f"B2: biped + tail, latency {tag} ms", "B2_tail_wide",
     dict(gait=dict(back=0.15), simkw=dict(stab_k=0.5, tail_alpha=0.17), servo=dict(latency=lat), push=STD_PUSH, T=13.0)),
], f"results/biped_vs_tail_{tag}ms.mp4")
print("ok")
