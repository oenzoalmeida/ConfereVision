"""Gera variações sintéticas determinísticas da foto de referência CC0.

As imagens derivadas medem a ROBUSTEZ do detector a perturbações controladas
(iluminação, oclusão, quantidade e transformações geométricas). São variações
de UMA única foto: não cobrem kits ou categorias reais e NÃO estimam acurácia.
Para regenerar: python exemplos/gerar_sinteticos.py
"""

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FONTE = ROOT / 'exemplos' / 'cafe-referencia.png'
DESTINO = ROOT / 'exemplos' / 'sinteticos'

# Caixas [x, y, w, h] anotadas manualmente na foto de referência.
XICARA = ('Caneca / xícara', [173, 18, 239, 292])
COLHER = ('Colher', [325, 66, 101, 262])


def _flip(imagem, objetos):
    largura = imagem.shape[1]
    invertidos = [(c, [largura - x - w, y, w, h]) for c, (x, y, w, h) in objetos]
    return cv2.flip(imagem, 1), invertidos


def _escala(imagem, objetos, fator):
    nova = cv2.resize(imagem, None, fx=fator, fy=fator, interpolation=cv2.INTER_AREA)
    escalonados = [
        (c, [round(x * fator), round(y * fator), round(w * fator), round(h * fator)])
        for c, (x, y, w, h) in objetos
    ]
    return nova, escalonados


def _brilho(imagem, objetos, alpha, beta):
    return cv2.convertScaleAbs(imagem, alpha=alpha, beta=beta), objetos


def _ruido(imagem, objetos, sigma=12.0):
    rng = np.random.default_rng(42)
    ruido = rng.normal(0, sigma, imagem.shape)
    return np.clip(imagem.astype(float) + ruido, 0, 255).astype(np.uint8), objetos


def _desfoque(imagem, objetos):
    return cv2.GaussianBlur(imagem, (5, 5), 0), objetos


def _oclusao(imagem, objetos, indice):
    classe, (x, y, w, h) = objetos[indice]
    barra_y0 = y + int(h * 0.35)
    barra_y1 = y + int(h * 0.65)
    imagem[barra_y0:barra_y1, x : x + w] = 0
    return imagem, objetos


def _duas_xicaras(imagem, objetos):
    # Cópia reduzida no canto inferior esquerdo, única região livre da foto
    # (não sobrepõe a xícara original nem a colher).
    classe, (x, y, w, h) = XICARA
    recorte = cv2.resize(imagem[y : y + h, x : x + w], None, fx=0.6, fy=0.6)
    ch, cw = recorte.shape[:2]
    destino_x, destino_y = 8, imagem.shape[0] - ch - 8
    imagem[destino_y : destino_y + ch, destino_x : destino_x + cw] = recorte
    return imagem, objetos + [(classe, [destino_x, destino_y, cw, ch])]


VARIACOES = {
    'brilho-escuro': lambda im, ob: _brilho(im, ob, 0.6, 0),
    'brilho-claro': lambda im, ob: _brilho(im, ob, 1.4, 0),
    'contraste-baixo': lambda im, ob: _brilho(im, ob, 0.7, 40),
    'ruido': _ruido,
    'desfoque': _desfoque,
    'flip-horizontal': _flip,
    'escala-80': lambda im, ob: _escala(im, ob, 0.8),
    'oclusao-xicara': lambda im, ob: _oclusao(im, ob, 0),
    'oclusao-colher': lambda im, ob: _oclusao(im, ob, 1),
    'duas-xicaras': _duas_xicaras,
}


def gerar(destino=DESTINO):
    base = cv2.imread(str(FONTE))
    if base is None:
        raise ValueError('Foto de referência não decodificada')
    destino.mkdir(parents=True, exist_ok=True)
    imagens = []
    for nome, variacao in VARIACOES.items():
        imagem, objetos = variacao(base.copy(), [XICARA, COLHER])
        arquivo = destino / f'{nome}.png'
        cv2.imwrite(str(arquivo), imagem)
        imagens.append(
            {
                'file': str(arquivo.relative_to(ROOT)),
                'sha256': hashlib.sha256(arquivo.read_bytes()).hexdigest(),
                'variacao': nome,
                'evaluated_classes': sorted({c for c, _ in objetos}),
                'objects': [{'classe': c, 'caixa': caixa} for c, caixa in objetos],
            }
        )
    rotulos = {
        'description': (
            'Variações sintéticas determinísticas de UMA foto CC0 (gerar_sinteticos.py). '
            'Medem robustez a perturbações controladas; não são fotos reais de kits e '
            'não estimam acurácia nem mAP.'
        ),
        'iou_threshold': 0.5,
        'confidence_threshold': 0.45,
        'images': imagens,
    }
    saida = destino / 'rotulos-sinteticos.json'
    saida.write_text(json.dumps(rotulos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return rotulos


if __name__ == '__main__':
    resultado = gerar()
    print(f"{len(resultado['images'])} imagens sintéticas em {DESTINO.relative_to(ROOT)}")
