"""Integration coverage using the checksum-verified ONNX model."""

import unittest
from pathlib import Path

import cv2
import numpy as np

from detector import PRODUCTS, detect_real


class RealModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (Path(__file__).parent / 'models' / 'yolox.onnx').is_file():
            raise RuntimeError('Run python download_model.py before the ONNX integration suite.')

    def test_blank_image_has_no_products(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        annotated, objects = detect_real(frame)
        self.assertEqual(objects, [])
        self.assertEqual(annotated.shape, frame.shape)
        self.assertEqual(annotated.dtype, np.uint8)

    def test_reference_image_is_repeatable_with_cached_model(self):
        frame = cv2.imread(str(Path(__file__).parent / 'exemplos' / 'correto.png'))
        self.assertIsNotNone(frame)
        first, objects = detect_real(frame)
        second, repeated = detect_real(frame)
        self.assertEqual(objects, repeated)
        np.testing.assert_array_equal(first, second)
        for obj in objects:
            self.assertIn(obj['classe'], PRODUCTS.values())
            self.assertGreaterEqual(obj['confidence'], 0.45)
            x, y, width, height = obj['caixa']
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertGreater(width, 0)
            self.assertGreater(height, 0)
            self.assertLessEqual(x + width, first.shape[1])
            self.assertLessEqual(y + height, first.shape[0])

    def test_reference_photograph_detects_the_annotated_cup(self):
        from evaluate_photos import evaluate

        result = evaluate()
        matches = result['images'][0]['matched']
        self.assertTrue(any(obj['classe'] == 'Caneca / xícara' for obj in matches))
        self.assertEqual(result['true_positives'] + result['false_negatives'], 2)

    def test_invalid_frame_is_rejected(self):
        with self.assertRaises(ValueError):
            detect_real(None)


if __name__ == '__main__':
    unittest.main()
