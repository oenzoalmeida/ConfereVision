import unittest
import cv2
import numpy as np
from vision import DEFAULT_KIT, sample, detect, compare

class VisionTests(unittest.TestCase):
    def check(self, kind):
        return compare(DEFAULT_KIT, detect(sample(kind))[2])
    def test_complete(self):
        self.assertTrue(self.check('correto')[0])
    def test_missing(self):
        ok, rows = self.check('faltando')
        self.assertFalse(ok)
        self.assertEqual(next(r['Diferença'] for r in rows if r['Classe'] == 'Verde / Círculo'), -1)
    def test_extra(self):
        self.assertFalse(self.check('extra')[0])
    def test_empty(self):
        objects = detect(np.full((400, 400, 3), 240, np.uint8))[2]
        self.assertEqual(objects, [])
        self.assertFalse(compare(DEFAULT_KIT, objects)[0])
    def test_unexpected_class(self):
        self.assertFalse(compare(DEFAULT_KIT, [{'classe':'Azul / Círculo'}])[0])
    def test_invalid(self):
        with self.assertRaises(ValueError): detect(None)
    def test_noise(self):
        im = sample()
        rng = np.random.default_rng(42)
        im = np.clip(im.astype(float) + rng.normal(0, 6, im.shape), 0, 255).astype(np.uint8)
        self.assertTrue(compare(DEFAULT_KIT, detect(im)[2])[0])

if __name__ == '__main__': unittest.main()
