"""Small, reproducible reference evaluation. Does not estimate production accuracy."""

import hashlib
import json
from pathlib import Path

import cv2

from detector import detect_real

ROOT = Path(__file__).resolve().parent


def iou(first, second):
    x, y, w, h = first
    other_x, other_y, other_w, other_h = second
    overlap = max(0, min(x + w, other_x + other_w) - max(x, other_x)) * max(
        0, min(y + h, other_y + other_h) - max(y, other_y)
    )
    union = w * h + other_w * other_h - overlap
    return overlap / union if union else 0


def evaluate():
    labels = json.loads((ROOT / 'exemplos/rotulos-fotograficos.json').read_text(encoding='utf-8'))
    true_positives = false_positives = false_negatives = 0
    images = []
    for entry in labels['images']:
        path = ROOT / entry['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Reference photograph checksum mismatch')
        frame = cv2.imread(str(path))
        if frame is None:
            raise ValueError('Reference photograph cannot be decoded')
        _, detected = detect_real(frame, threshold=labels['confidence_threshold'])
        candidates = [obj for obj in detected if obj['classe'] in entry['evaluated_classes']]
        unmatched = list(entry['objects'])
        matched = []
        for prediction in sorted(candidates, key=lambda obj: obj['confidence'], reverse=True):
            same_class = [obj for obj in unmatched if obj['classe'] == prediction['classe']]
            best = max(
                same_class, key=lambda obj: iou(obj['caixa'], prediction['caixa']), default=None
            )
            if (
                best is not None
                and iou(best['caixa'], prediction['caixa']) >= labels['iou_threshold']
            ):
                unmatched.remove(best)
                matched.append(
                    {
                        'classe': best['classe'],
                        'iou': round(iou(best['caixa'], prediction['caixa']), 4),
                    }
                )
                true_positives += 1
            else:
                false_positives += 1
        false_negatives += len(unmatched)
        images.append(
            {
                'file': entry['file'],
                'detections': candidates,
                'matched': matched,
                'missed': unmatched,
            }
        )
    predicted = true_positives + false_positives
    expected = true_positives + false_negatives
    return {
        'scope': 'One reference photo, two annotated objects. Not representative. No mAP estimate.',
        'confidence_threshold': labels['confidence_threshold'],
        'iou_threshold': labels['iou_threshold'],
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'precision': true_positives / predicted if predicted else None,
        'recall': true_positives / expected if expected else None,
        'images': images,
    }


if __name__ == '__main__':
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
