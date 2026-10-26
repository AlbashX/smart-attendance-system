"""Model-independent decisions and evaluation. Similarities are not probabilities."""
import numpy as np


def normalize(vector):
    v = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = np.linalg.norm(v)
    if not np.isfinite(v).all() or norm < 1e-8:
        raise ValueError('Invalid embedding')
    return v / norm


def match(vector, gallery, threshold=.45, margin=.08):
    ranked = sorted(((key, float(np.clip(np.dot(vector, normalize(value)), -1, 1)))
                     for key, value in gallery.items()), key=lambda x: x[1], reverse=True)
    if not ranked:
        return dict(identity=None, score=None, gap=None, reason='No volunteers enrolled', scores={})
    key, score = ranked[0]
    gap = score - ranked[1][1] if len(ranked) > 1 else 2.
    accepted = score >= threshold and gap >= margin
    return dict(identity=key if accepted else None, score=score, gap=gap,
                reason='Match' if accepted else ('Ambiguous match' if score >= threshold else 'Unknown'),
                scores=dict(ranked))


class Stability:
    def __init__(self):
        self.identity = None
        self.count = 0
        self.last = 0.

    def observe(self, identity, now):
        self.count = self.count + 1 if identity and identity == self.identity and now-self.last < 2 else (1 if identity else 0)
        self.identity, self.last = identity, now
        return self.count >= 3


def verification_metrics(genuine, impostor, threshold):
    g, i = np.asarray(genuine), np.asarray(impostor)
    return dict(genuine_count=len(g), impostor_count=len(i),
                far=float(np.mean(i >= threshold)) if len(i) else None,
                frr=float(np.mean(g < threshold)) if len(g) else None,
                accuracy=float(((g >= threshold).sum() + (i < threshold).sum()) / (len(g)+len(i))) if len(g)+len(i) else None)


def calibrate(genuine, impostor, target_far=.01):
    if not len(genuine) or not len(impostor):
        raise ValueError('Both genuine and impostor validation attempts are required')
    # Include just-above endpoints so a zero observed FAR solution is possible.
    candidates = sorted(set([-1., 1.000001] + [float(x) for x in genuine+impostor] + [float(x)+1e-6 for x in impostor]))
    valid = [t for t in candidates if np.mean(np.asarray(impostor) >= t) <= target_far]
    return min(valid, key=lambda t: (np.mean(np.asarray(genuine) < t), t))
