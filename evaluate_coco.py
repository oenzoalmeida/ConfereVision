"""Avaliação do detector em fotos reais e variadas do COCO val2017.

Contexto: evaluate_photos.py mede robustez em variações de UMA foto de
referência (controlada). Este script mede o detector YOLOX-s em centenas de
fotos públicas variadas das categorias do catálogo. É um degrau acima em
representatividade, mas AINDA NÃO é validação de precisão comercial: as fotos
do COCO não são kits/bancadas dos usuários e a amostra é limitada.

Fonte dos dados: COCO val2017 (https://cocodataset.org), anotações de
instância oficiais. Licença das imagens: conforme cada foto do COCO (Flickr);
uso aqui apenas para avaliação local, sem redistribuição no repositório.

Uso:
    python download_model.py          # uma vez: baixa e valida o YOLOX-s
    python evaluate_coco.py           # baixa anotações/imagens (1ª vez) e avalia
    python evaluate_coco.py --max-por-classe 40 --max-imagens 800

Saída: resumo no terminal e relatório completo em
docs/avaliacao-coco-resultado.json.
"""

import argparse
import json
import pathlib
import random
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

import cv2

from detector import PRODUCTS, detect_real

ROOT = Path(__file__).resolve().parent
DATASETS = ROOT / 'datasets'
ANNOTATIONS = DATASETS / 'annotations' / 'instances_val2017.json'
ANNOTATIONS_ZIP = 'http://images.cocodataset.org/annotations/annotations_trainval2017.zip'
IMAGE_URL = 'http://images.cocodataset.org/val2017/{file_name}'
IMAGES_DIR = DATASETS / 'val2017'
REPORT = ROOT / 'docs' / 'avaliacao-coco-resultado.json'

CONFIDENCE = 0.45  # mesmo limiar de produção (README)
IOU_THRESHOLD = 0.5
SEED = 20261102

# Índice contínuo do modelo (coco80) -> nome oficial COCO em inglês.
# As chaves são as mesmas de detector.PRODUCTS; o id numérico no JSON de
# anotações do COCO NÃO é esse índice — ele é resolvido pelo nome.
COCO80_NAMES = {
    24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase',
    39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife',
    44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 49: 'orange',
    63: 'laptop', 64: 'mouse', 65: 'remote', 66: 'keyboard', 67: 'cell phone',
    73: 'book', 74: 'clock', 75: 'vase', 76: 'scissors', 77: 'teddy bear',
    79: 'toothbrush',
}
assert set(COCO80_NAMES) == set(PRODUCTS), 'Cobertura de categorias diverge do detector'


def iou(first, second):
    x, y, w, h = first
    ox, oy, ow, oh = second
    overlap = max(0, min(x + w, ox + ow) - max(x, ox)) * max(0, min(y + h, oy + oh) - max(y, oy))
    union = w * h + ow * oh - overlap
    return overlap / union if union else 0


def ensure_annotations():
    if ANNOTATIONS.exists():
        return
    DATASETS.mkdir(exist_ok=True)
    tmp = DATASETS / 'annotations_trainval2017.zip'
    print('Baixando anotações COCO val2017 (~250 MB)...')
    urllib.request.urlretrieve(ANNOTATIONS_ZIP, tmp)
    with zipfile.ZipFile(tmp) as zf:
        zf.extract('annotations/instances_val2017.json', DATASETS)
    tmp.unlink()


def ensure_image(file_name):
    path = IMAGES_DIR / file_name
    if not path.exists():
        urllib.request.urlretrieve(IMAGE_URL.format(file_name=file_name), path)
    return path


def select_images(annotations, max_por_classe, max_imagens):
    by_cat = defaultdict(list)
    for ann in annotations['annotations']:
        if not ann.get('iscrowd'):
            by_cat[ann['category_id']].append(ann['image_id'])
    rng = random.Random(SEED)
    chosen = []
    for cat_id in sorted(by_cat):
        ids = sorted(set(by_cat[cat_id]))
        rng.shuffle(ids)
        chosen.extend(ids[:max_por_classe])
    unique = sorted(set(chosen))
    rng.shuffle(unique)
    return set(unique[:max_imagens])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-por-classe', type=int, default=15)
    parser.add_argument('--max-imagens', type=int, default=300)
    parser.add_argument('--inicio', type=int, default=0, help='fatia inicial (0-based) das imagens selecionadas')
    parser.add_argument('--fim', type=int, default=None, help='fatia final exclusiva; padrão: todas')
    parser.add_argument('--parcial', type=str, default=None, help='grava contagens da fatia neste JSON em vez de agregar')
    args = parser.parse_args()

    ensure_annotations()
    data = json.loads(ANNOTATIONS.read_text(encoding='utf-8'))
    if len(data['images']) != 5000 or len(data['categories']) != 80:
        raise RuntimeError('Arquivo de anotações inesperado; verifique a fonte COCO val2017.')

    # Resolve o id do JSON pelo nome oficial da categoria (os ids do JSON
    # não são os índices contínuos usados pelo modelo).
    json_id_by_name = {c['name']: c['id'] for c in data['categories']}
    label_by_json_id = {}
    for index, english in COCO80_NAMES.items():
        if english not in json_id_by_name:
            raise RuntimeError(f'Categoria COCO ausente no arquivo: {english}')
        label_by_json_id[json_id_by_name[english]] = PRODUCTS[index]

    selected = select_images(data, args.max_por_classe, args.max_imagens)
    ordered_ids = sorted(img['id'] for img in data['images'] if img['id'] in selected)
    fatia = ordered_ids[args.inicio:args.fim]
    images = {img['id']: img for img in data['images'] if img['id'] in set(fatia)}
    gt_by_image = defaultdict(list)
    for ann in data['annotations']:
        if ann['image_id'] in selected and ann['category_id'] in label_by_json_id and not ann.get('iscrowd'):
            gt_by_image[ann['image_id']].append(
                {'classe': label_by_json_id[ann['category_id']], 'caixa': [round(v) for v in ann['bbox']]}
            )

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    total = {'tp': 0, 'fp': 0, 'fn': 0}
    per_class = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'suporte': 0})
    evaluated = 0
    for n, (image_id, img) in enumerate(sorted(images.items()), 1):
        path = ensure_image(img['file_name'])
        frame = cv2.imread(str(path))
        if frame is None:
            continue
        ground_truth = gt_by_image.get(image_id, [])
        _, detected = detect_real(frame, threshold=CONFIDENCE)
        candidates = [o for o in detected if o['classe'] in set(PRODUCTS.values())]
        unmatched = list(ground_truth)
        for prediction in sorted(candidates, key=lambda o: o['confidence'], reverse=True):
            same = [o for o in unmatched if o['classe'] == prediction['classe']]
            best = max(same, key=lambda o: iou(o['caixa'], prediction['caixa']), default=None)
            stats = per_class[prediction['classe']]
            if best is not None and iou(best['caixa'], prediction['caixa']) >= IOU_THRESHOLD:
                unmatched.remove(best)
                stats['tp'] += 1
                total['tp'] += 1
            else:
                stats['fp'] += 1
                total['fp'] += 1
        for miss in unmatched:
            per_class[miss['classe']]['fn'] += 1
            total['fn'] += 1
        evaluated += 1
        if n % 50 == 0:
            print(f'{n}/{len(images)} imagens...', flush=True)

    for classe, stats in per_class.items():
        stats['suporte'] = stats['tp'] + stats['fn']

    if args.parcial:
        pathlib.Path(args.parcial).write_text(json.dumps({
            'inicio': args.inicio, 'fim': args.inicio + evaluated,
            'avaliadas': evaluated, 'total': total,
            'por_classe': {k: dict(v) for k, v in per_class.items()},
        }), encoding='utf-8')
        print(f'fatia {args.inicio}:{args.inicio + evaluated} avaliada ({evaluated} imagens)')
        return

    def rates(stats):
        tp, fp, fn = stats['tp'], stats['fp'], stats['fn']
        return {
            'precisao': round(tp / (tp + fp), 3) if tp + fp else None,
            'revocacao': round(tp / (tp + fn), 3) if tp + fn else None,
        }

    report = {
        'dataset': 'COCO val2017 (anotações oficiais de instância)',
        'amostra': {
            'imagens_avaliadas': evaluated,
            'max_por_classe': args.max_por_classe,
            'max_imagens': args.max_imagens,
            'semente': SEED,
        },
        'limiar_confianca': CONFIDENCE,
        'limiar_iou': IOU_THRESHOLD,
        'total': {**total, **rates(total)},
        'por_classe': {k: {**v, **rates(v)} for k, v in sorted(per_class.items())},
        'escopo': (
            'Fotos públicas variadas, não kits reais de usuários. Mede o detector '
            'nas categorias do catálogo em cenário geral; não é validação comercial.'
        ),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"\nImagens avaliadas: {evaluated}  (confiança>={CONFIDENCE}, IoU>={IOU_THRESHOLD})")
    print(f"TOTAL  TP={total['tp']} FP={total['fp']} FN={total['fn']}  "
          f"precisão={report['total']['precisao']}  revocação={report['total']['revocacao']}")
    for classe, stats in report['por_classe'].items():
        print(f"  {classe:<18} TP={stats['tp']:<4} FP={stats['fp']:<4} FN={stats['fn']:<4} "
              f"P={stats['precisao']} R={stats['revocacao']}")
    print(f'Relatório: {REPORT}')


if __name__ == '__main__':
    main()
