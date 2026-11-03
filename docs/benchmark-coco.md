# Avaliação em fotos variadas (COCO val2017)

`evaluate_coco.py` mede o detector YOLOX-s em fotos públicas reais e variadas
das 26 categorias do catálogo — um degrau de representatividade acima das
variações sintéticas de uma única foto (`evaluate_photos.py`).

## O que isto é — e o que não é

- **É**: uma medida honesta do detector em cenários gerais variados, com
  centenas de fotos e milhares de objetos anotados.
- **Não é**: validação de precisão comercial. As fotos do COCO não são
  kits/bancadas dos usuários; o uso real (foto de kit em bancada, iluminação
  e enquadramento típicos) tende a resultados diferentes. Uma validação
  comercial exige um conjunto de fotos reais dos kits dos usuários com
  gabarito conferido.

## Metodologia

- Fonte: COCO val2017, anotações oficiais de instância (5000 imagens).
  As imagens são baixadas localmente e não entram no repositório.
- Amostra: até 15 imagens por categoria do catálogo, no máximo 300 imagens,
  semente fixa 20261102 (seleção reproduzível).
- Detecção: `detector.detect_real` no limiar de produção (confiança 0,45).
- Correspondência: mesma regra de `evaluate_photos.py` — greedy por
  confiança, mesma classe, IoU ≥ 0,5; anotações `iscrowd` ignoradas.
- Os índices contínuos do modelo (coco80) são resolvidos para os ids do
  JSON de anotações pelo nome oficial da categoria — os dois espaços de ids
  são diferentes.

## Resultado (300 imagens, 935 objetos anotados nas categorias do catálogo)

- Total: TP=271, FP=111, FN=664 — **precisão 0,709**, **revocação 0,290**.
- Leitura: quando o sistema aponta um objeto, ele acerta na maioria das
  vezes (precisão ~71%); porém deixa passar muitos objetos presentes
  (revocação ~29%). Objetos pequenos ou parcialmente oclusos em cena geral
  são os mais perdidos — em bancada controlada com kit organizado, a
  revocação tende a ser melhor, o que só fotos reais de kits confirmam.
- Detalhe por classe: `docs/avaliacao-coco-resultado.json`.

## Como reproduzir

```bash
python download_model.py
python evaluate_coco.py   # baixa anotações/imagens na 1ª execução
```

Execução em fatias (ambiente com tempo limitado por chamada):

```bash
python evaluate_coco.py --inicio 0 --fim 150 --parcial /tmp/p1.json
python evaluate_coco.py --inicio 150 --parcial /tmp/p2.json
```
