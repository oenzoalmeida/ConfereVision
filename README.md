# ConfereVision

Sistema web de conferência visual de kits: o usuário cadastra um kit com as quantidades esperadas de cada item, envia uma foto ou um vídeo e a aplicação detecta os objetos presentes, compara com o esperado e aponta faltas e excedentes. O histórico é privado por usuário.

A detecção é real, feita no servidor com o modelo **YOLOX-s (OpenCV Zoo)** em CPU, sem serviços de IA pagos. O projeto foi construído em Python com Django e PostgreSQL.

## Demonstração

**Aplicação:** https://conferevision.vercel.app

> A demo roda na Vercel (função Python com o modelo ONNX embarcado). O endpoint [`/healthz`](https://conferevision.vercel.app/healthz) indica o estado do serviço.

## Sobre o projeto

A conferência manual de kits (pedidos, envelopes, kits de peças) é propensa a esquecimentos. O ConfereVision organiza essa checagem: cada kit tem uma composição esperada (item → quantidade) e cada análise compara a detecção da imagem/vídeo contra essa composição, registrando o resultado no histórico do usuário.

O sistema tem autenticação, área própria por usuário (kits, análises e imagens anotadas isolados por titularidade), administração com indicadores e exportação de histórico.

## Principais funcionalidades

Cadastro de kits com composição esperada (item → quantidade).

Conferência por **imagem** (JPEG/PNG até 16 MP e 30 MB, com correção de orientação EXIF) ou **vídeo** (até 30 MB, até 4K, primeiros 15 segundos, amostras de ~1 s, aprovação exige as três últimas amostras compatíveis).

Detecção de objetos real com YOLOX-s e limiar de confiança 0,45, com 26 categorias do catálogo expostas para composição (garrafa, caneca, mouse, teclado, livro, entre outras).

Resultado com diferenças apontadas: faltas, excedentes e contagens. Registro de confirmação do usuário.

Histórico privado por usuário, com imagens anotadas salvas no banco e exportação.

Cadastro público (somente usuários comuns), recuperação de senha por código secreto rotativo e painel administrativo (`/administracao/`) com indicadores, gestão de usuários e redefinição de senhas.

Limite de tentativas no login público e na recuperação, e limite de análises por usuário.

## Tecnologias

Python 3.12, Django 5.2 (MVC, sessões, autenticação, CSRF).

OpenCV (DNN) + **YOLOX-s ONNX** do [OpenCV Zoo](https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_yolox): inferência em CPU.

PostgreSQL (produção) / SQLite (desenvolvimento local).

Gunicorn, WhiteNoise (estáticos).

Vercel (hospedagem serverless), Neon (PostgreSQL persistente).

## Arquitetura / Estrutura

```text
ConfereVision/
├── config/            # settings e URLs do Django
├── core/              # modelos, views, templates e testes da aplicação
├── vision.py          # pipeline de detecção real (YOLOX/OpenCV DNN)
├── detector.py        # decoding adaptado do OpenCV Zoo
├── test_vision.py     # testes de visão (fluxo geométrico)
├── download_model.py  # download do modelo com validação SHA-256
├── exemplos/          # imagens/vídeo de exemplo e créditos
├── vercel.json, api/ (adaptador WSGI)
└── manage.py, requirements.txt
```

A inferência roda no servidor. As imagens anotadas ficam no banco, protegidas por login e verificação de titularidade no servidor.

## Como executar

Requisitos: Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python download_model.py         # baixa o YOLOX-s e valida o SHA-256
cp .env.example .env             # defina SECRET_KEY (local: DEBUG=1)
python manage.py migrate
python manage.py bootstrap_admin # cria o administrador inicial
python manage.py collectstatic --noinput
python manage.py runserver
```

Acesse `http://127.0.0.1:8000`. No Windows há também o `iniciar_windows.bat` de conveniência. Uma instalação limpa cria as credenciais iniciais pelo comando `bootstrap_admin` (que não substitui senhas de contas existentes). A troca da senha inicial é obrigatória no primeiro acesso.

## Variáveis de ambiente

Definidas em `.env` a partir de `.env.example` (nunca comunique valores reais):

| Variável | Descrição |
|---|---|
| `DEBUG` | `1` em desenvolvimento. Produção exige `0` |
| `SECRET_KEY` | Chave secreta do Django (gere com `python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `ALLOWED_HOSTS` | Hostnames em produção, separados por vírgula (ex.: `conferevision.vercel.app`) |
| `DATABASE_URL` | PostgreSQL persistente em produção (ex.: `postgres://usuario:senha@host:5432/conferevision`) |
| `ADMIN_USERNAME` / `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Criação do administrador pelo `bootstrap_admin` |

A aplicação bloqueia a inicialização em produção sem `DATABASE_URL` e `SECRET_KEY`.

## Exemplos e avaliação

Os exemplos ficam em `exemplos/`:

`correto.png`, `faltando.png`, `extra.png`: imagens sintéticas para o kit geométrico do fluxo HSV/contornos.

`demonstracao.avi`: vídeo de teste com transições correto/falta/correto.

`cafe-referencia.png`: foto de referência (scikit-image): o modelo identificou uma xícara com escore 0,836 e **não detectou a colher** (teste pontual, não uma métrica de precisão do sistema).

`frutas-opencv.jpg`: exemplo de falha: nenhuma detecção acima do limiar em frutas cortadas e sobrepostas.

Testes automatizados:

```bash
python manage.py test core         # 16 testes de aplicação/segurança
python -m unittest -v test_vision  # 7 testes de visão geométrica
```

A avaliação reproduzível de `python evaluate_photos.py` usa `exemplos/rotulos-fotograficos.json`, com caixas manuais para a xícara e a colher da foto de café. A correspondência exige a mesma classe e IoU de pelo menos 0,50, com confiança mínima de 0,45. O pires está fora das classes avaliadas. O arquivo da foto é verificado por SHA-256.

Com o modelo atual, esse único exemplo teve um verdadeiro positivo (xícara), nenhum falso positivo e um falso negativo (colher). A precisão observada foi 1,00 e o recall foi 0,50 nesses dois objetos. Esses valores não estimam a qualidade geral do sistema. A amostra não cobre diversidade de produtos, iluminação, oclusão ou distância. Não há estimativa de mAP. O teste automatizado exige a detecção da xícara e permite melhorias futuras na detecção da colher.

Não foi feita avaliação representativa de acurácia ou de carga multiusuário.

## Status

Versão estável publicada em https://conferevision.vercel.app (função Python na Vercel, cold start de ~2s), com PostgreSQL persistente no Neon e HTTPS ativo. A fase anterior de hospedagem no Render foi encerrada em 2026-10.

## Limitações conhecidas

O detector reconhece apenas as 26 categorias do catálogo. Não identifica marcas, modelos, SKU ou objetos arbitrários. Um objeto não detectado não pode ser conferido.

A classe "livro" não garante reconhecimento de cadernos. "caneca/xícara" não verifica conteúdo.

Sem contagem acumulada ou rastreamento em vídeos: eventos entre amostras podem passar despercebidos. O processamento tem limite aproximado de 65 segundos.

Não há envio de e-mail, verificação de titularidade de e-mail, CAPTCHA, quotas de armazenamento, política automática de retenção ou monitoramento operacional. Não auditada para uso comercial.

Uso como aprovação autônoma de expedição não é recomendado.

## Segurança e dados

As senhas são armazenadas com hash, e as sessões ficam no banco. Os formulários usam proteção CSRF, com cookies restritos à sessão e ao CSRF.

A titularidade dos recursos é verificada no servidor, inclusive no acesso a imagens. Há limites de tentativas no login e na recuperação de senha, além de um limite de análises por usuário.

Sem rastreamento, publicidade ou analytics.

## Referências e licenças

[OpenCV Zoo YOLOX](https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_yolox): Apache 2.0 (licença em `models/LICENSE`, com decodificação adaptada deste projeto).

[YOLOX: Exceeding YOLO Series](https://arxiv.org/abs/2107.08430).

[Segmentação HSV (OpenCV)](https://docs.opencv.org/4.x/da/d97/tutorial_threshold_inRange.html).

[Django 5.2](https://docs.djangoproject.com/en/5.2/).

Imagem café: scikit-image v0.21.0, `skimage/data/coffee.png` (créditos em `exemplos/CREDITOS.txt`). Imagem frutas: [exemplo do OpenCV](https://github.com/opencv/opencv/blob/master/samples/data/fruits.jpg), somente referência de teste.

## Autor

Enzo Almeida
