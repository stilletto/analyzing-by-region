"""Render recorded runs to MP4 (software OpenGL via OSMesa)."""
import os
os.environ.setdefault("MUJOCO_GL", "osmesa")
os.environ.setdefault("PYOPENGL_PLATFORM", "osmesa")
import subprocess
import numpy as np
import mujoco
from PIL import Image, ImageDraw, ImageFont

from experiments import VARIANTS, ZC, PZ
from sim import Robot, GaitPlan, Sim, ServoSpec


def _font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def record(variant, gait=None, simkw=None, servo=None, push=None, T=None):
    v = VARIANTS[variant]
    r = Robot(v["tail"] if v["tail"] is None else dict(v["tail"]))
    gait = dict(gait or {})
    if v["tail"] is not None:
        gait.setdefault("t_start", 4.5)
    plan = GaitPlan(v["mode"], ZC, PZ, **gait)
    spec = ServoSpec().scaled(**(servo or {}))
    pushes = [(tp + plan.t_start, dur, np.array(F, float)) for (tp, dur, F) in (push or [])]
    s = Sim(r, spec, plan, push=pushes, record=True, **(simkw or {}))
    res = s.run(T=T, stop_on_fall=False)
    return r, s, res, pushes


def render_frames(r, frames, pushes, w=640, h=480, label="", fps=30, t_offset=0.0, dt_frame=0.033):
    m = r.m
    d = mujoco.MjData(m)
    ren = mujoco.Renderer(m, h, w)
    cam = mujoco.MjvCamera()
    cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.distance = 3.4
    cam.azimuth = 125
    cam.elevation = -12
    font = _font(20)
    fsmall = _font(16)
    imgs = []
    look = None
    for i, q in enumerate(frames):
        t = i * dt_frame
        d.qpos[:] = q
        mujoco.mj_forward(m, d)
        target = np.array([d.qpos[0], 0.0, 0.75])
        look = target if look is None else 0.9 * look + 0.1 * target
        cam.lookat[:] = look
        ren.update_scene(d, cam)
        img = Image.fromarray(ren.render())
        dr = ImageDraw.Draw(img)
        dr.text((12, 10), label, fill=(20, 20, 30), font=font)
        dr.text((12, 38), "t = %.1f s" % t, fill=(40, 40, 60), font=fsmall)
        for (tp, dur, F) in pushes:
            if tp <= t < tp + dur + 0.25:
                dr.text((12, 60), "PUSH %s N" % np.round(F).astype(int).tolist(), fill=(200, 30, 30), font=font)
        if d.qpos[2] < 0.45 or d.xmat[r.pelvis].reshape(3, 3)[2, 2] < 0.6:
            dr.text((w // 2 - 60, h // 2 - 20), "FALL", fill=(200, 30, 30), font=_font(40))
        imgs.append(np.asarray(img))
    ren.close()
    return imgs


def write_mp4(imgs, path, fps=30):
    h, w, _ = imgs[0].shape
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{w}x{h}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                          "-crf", "26", path], stdin=subprocess.PIPE)
    for im in imgs:
        p.stdin.write(im.tobytes())
    p.stdin.close()
    p.wait()


def side_by_side(runs, path, w=560, h=420):
    """runs: list of (label, variant, kwargs). Renders each and stacks horizontally."""
    all_imgs = []
    for label, variant, kw in runs:
        r, s, res, pushes = record(variant, **kw)
        all_imgs.append(render_frames(r, s.frames, pushes, w, h, label))
    n = min(len(a) for a in all_imgs)
    combo = [np.concatenate([a[i] for a in all_imgs], axis=1) for i in range(n)]
    write_mp4(combo, path)
    return path
