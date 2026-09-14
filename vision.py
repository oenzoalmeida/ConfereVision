"""Detecção geométrica em bancada controlada; não reconhece SKUs."""
from collections import Counter
import cv2
import numpy as np

COLORS = {'Azul': (90, 130), 'Verde': (36, 85), 'Amarelo': (20, 35)}
SHAPES = ['Retângulo', 'Círculo', 'Triângulo']

def detect(frame, min_area=600):
    if frame is None or frame.size == 0:
        raise ValueError('Imagem inválida.')
    scale = min(1, 1200 / max(frame.shape[:2]))
    frame = cv2.resize(frame, None, fx=scale, fy=scale)
    hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (5, 5), 0), cv2.COLOR_BGR2HSV)
    combined = np.zeros(frame.shape[:2], np.uint8)
    annotated = frame.copy()
    objects = []
    for color, (lo, hi) in COLORS.items():
        mask = cv2.inRange(hsv, (lo, 85, 55), (hi, 255, 255))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        combined = cv2.bitwise_or(combined, mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            perimeter = cv2.arcLength(contour, True)
            poly = cv2.approxPolyDP(contour, .025 * perimeter, True)
            circularity = 4 * np.pi * area / max(perimeter ** 2, 1)
            shape = ('Triângulo' if len(poly) == 3 else 'Retângulo' if len(poly) == 4
                     else 'Círculo' if circularity > .78 else 'Não classificado')
            label = f'{color} / {shape}'
            x, y, w, h = cv2.boundingRect(contour)
            objects.append({'classe': label, 'area': round(area), 'caixa': [x, y, w, h]})
            cv2.rectangle(annotated, (x, y), (x+w, y+h), (60, 180, 50), 2)
            ascii_label = label.encode('ascii', 'ignore').decode()
            cv2.putText(annotated, ascii_label, (x, max(y-8, 20)), cv2.FONT_HERSHEY_SIMPLEX, .5, (30, 60, 30), 2)
    return annotated, combined, objects

def compare(expected, objects):
    counts = Counter(o['classe'] for o in objects)
    rows = [{'Classe': key, 'Esperado': int(expected.get(key, 0)),
             'Detectado': counts[key], 'Diferença': counts[key] - int(expected.get(key, 0))}
            for key in sorted(set(expected) | set(counts))]
    return bool(expected) and all(r['Diferença'] == 0 for r in rows), rows

def sample(kind='correto'):
    image = np.full((600, 900, 3), 245, np.uint8)
    cv2.rectangle(image, (80, 140), (260, 420), (210, 90, 25), -1)
    if kind != 'faltando':
        cv2.circle(image, (470, 290), 90, (40, 170, 40), -1)
    pts = np.array([[700, 150], [600, 420], [820, 420]])
    cv2.fillPoly(image, [pts], (20, 220, 240))
    if kind == 'extra':
        cv2.circle(image, (460, 510), 42, (40, 170, 40), -1)
    return image

DEFAULT_KIT = {'Azul / Retângulo': 1, 'Verde / Círculo': 1, 'Amarelo / Triângulo': 1}
