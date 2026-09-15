# ConfereVision — versão 2

Conferência visual de kits em Python, Django e OpenCV, com usuários, administração, detecção real YOLOX, imagens, vídeos e histórico privado.

## Situação desta entrega
Versão final estável (v1.0), publicada e em produção. Código: https://github.com/oenzoalmeida/ConfereVision. Aplicação publicada no Render: https://conferevision.onrender.com, com PostgreSQL persistente no Neon e HTTPS ativo (`/healthz` disponível para verificação). Não é um produto comercial validado nem substitui os documentos acadêmicos exigidos pela APS.

## Arquitetura
- **Django 5.2** (MVC, sessões, autenticação e CSRF) servido por **Gunicorn**.
- **Render** como hospedagem (plano Free, deploy via `render.yaml`/`build.sh`, HTTPS e health check automáticos).
- **PostgreSQL no Neon** como banco persistente (imagens anotadas e histórico incluídos no banco).
- **OpenCV + YOLOX-s ONNX** (OpenCV Zoo, CPU) para detecção de objetos; estáticos servidos por WhiteNoise.

## Abrir no Windows
1. Instale Python 3.12.
2. Extraia todo o ZIP, preservando as pastas.
3. Execute `iniciar_windows.bat`.
4. Acesse http://127.0.0.1:8000.
5. Use as credenciais privadas de `ACESSO_ADMIN.txt`. A troca da senha inicial é obrigatória.

O ZIP privado inclui um SQLite local contendo apenas o administrador e dois kits iniciais, além do arquivo de acesso. Não publique esse ZIP em repositório público. O `.gitignore` exclui banco e credenciais ao versionar o código. Uma instalação limpa cria novas credenciais pelo comando `bootstrap_admin`; o comando não substitui senhas de contas existentes.

Para macOS/Linux:
```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python download_model.py
python manage.py migrate
python manage.py bootstrap_admin
python manage.py collectstatic --noinput
python manage.py runserver
```

O modelo está incluído neste ZIP. O script valida o SHA-256 e só baixa de novo se necessário. Não há API de IA paga. A inferência roda no servidor, com OpenCV DNN e CPU.

## Contas
- Cadastro público cria exclusivamente usuários comuns.
- Usuários acessam apenas seus kits, análises e imagens.
- Administração: `/administracao/` e `/admin/`, com permissão do servidor.
- Administrador pode consultar indicadores, gerenciar usuários, desativar contas e redefinir senhas.
- `admin@conferevision.invalid` é um identificador reservado fictício, NÃO uma caixa de e-mail criada ou um domínio registrado. O login inicial é `administrador`.
- Recuperação usa um código secreto mostrado uma vez no cadastro. Ao usar o código, a senha é alterada e o código é rotacionado. Guarde o novo código. Sem o código, solicite redefinição ao administrador.
- A senha inicial do administrador exige alteração antes de acessar qualquer outra tela.
- Não há envio de e-mail ou verificação de titularidade de e-mail nesta versão.

## Fluxo
Cadastre um kit e as quantidades esperadas; escolha Conferir kit; envie uma imagem ou um vídeo; consulte objetos detectados e diferenças; registre se o resultado foi correto; consulte ou exporte o histórico.
As inspeções são salvas automaticamente, com a composição e o resultado daquela análise. Alterar um kit não altera resultados antigos.

## Detecção
**Real:** YOLOX-s COCO via OpenCV Zoo, com 26 categorias de objetos expostas para composição (garrafa, caneca, mouse, teclado, livro, entre outras). O limiar de confiança do detector é 0,45. Pessoas, móveis e categorias fora do catálogo não entram na comparação. Objetos de qualquer categoria do catálogo são contados, mesmo que não tenham sido previstos no kit, permitindo identificar excedentes.
**Geométrica:** segmentação HSV, operações morfológicas, contornos, classificação por forma e contagem. As imagens sintéticas demonstram esse fluxo e não simulam detecção semântica.

A classe Livro não garante reconhecimento de cadernos. Caneca/xícara não verifica conteúdo. O detector não identifica marcas, modelo, SKU ou qualquer objeto arbitrário. Um objeto não detectado não pode ser conferido. Não use como aprovação autônoma de expedição.

**Vídeos:** até 30 MB, resolução até 4K, FPS entre 1 e 120; primeiros 15 segundos; amostras de cerca de 1 segundo; aprovação exige as três últimas amostras compatíveis. A tabela de composição é a última amostra. Não há contagem acumulada ou rastreamento; eventos entre amostras podem passar despercebidos. Processamento tem limite aproximado de 65 segundos.
**Imagens:** JPEG/PNG até 16 MP e 30 MB; orientação EXIF corrigida.

## Exemplos e avaliação
- correto.png, faltando.png e extra.png: imagens sintéticas para kit geométrico padrão.
- demonstracao.avi: três segundos corretos, três com falta, três corretos.
- cafe-referencia.png: foto de referência do scikit-image. O modelo identificou uma xícara com escore 0,836, mas não detectou a colher. Isso é um teste pontual, NÃO 83,6% de precisão do sistema.
- frutas-opencv.jpg: exemplo de falha: nenhuma detecção acima de 0,45 em frutas cortadas e sobrepostas.

Testes:
```
python manage.py test core
python -m unittest test_vision -v
```
Foram aprovados 16 testes de aplicação/segurança e 7 de visão geométrica. Também foi verificado o vídeo sintético, incluindo as transições. O detector real rodou na foto da xícara; o pico do processo isolado foi cerca de 174 MiB no ambiente de teste. Não foi feita avaliação representativa de acurácia ou carga multiusuário. Verificação visual via navegador foi bloqueada pelo ambiente; rotas e templates foram verificados pelos testes Django.

## Deploy (já realizado)
A aplicação está publicada em **https://conferevision.onrender.com** (Render, plano Free, auto-deploy a partir da branch `main`), com **PostgreSQL persistente no Neon** via `DATABASE_URL` e HTTPS ativo. O `/healthz` responde o estado do serviço.

Arquivos `render.yaml` e `build.sh` descrevem o serviço. Não há recursos pagos no manifesto. O aplicativo bloqueia inicialização em produção sem DATABASE_URL e SECRET_KEY. Os arquivos grandes de modelo ficam fora do git; o build baixa e verifica o SHA-256.

Para recriar o deploy em outra conta:
1. Disponibilizar este código em repositório GitHub, sem banco e credenciais.
2. Conectar um PostgreSQL persistente compatível (Neon ou equivalente; o PostgreSQL gratuito do próprio Render expira em 30 dias).
3. Criar o Blueprint Free e informar DATABASE_URL, SECRET_KEY, ADMIN_PASSWORD e demais variáveis do `.env.example`. Não publique segredos no GitHub.
4. Conferir HTTPS, `/healthz`, cadastro, acesso administrativo e uma análise real após publicar.

Limitações conhecidas do plano gratuito: o serviço hiberna após 15 minutos sem tráfego e pode levar cerca de um minuto para voltar; CPU/RAM são compartilhadas e o processamento de vídeo tem limite aproximado de 65 segundos (ver seção Vídeos). Consulte limites de consumo: https://render.com/docs/free.

## Segurança e dados
Django protege senhas com hash, sessões no banco e formulários com CSRF. Verificações de propriedade são feitas no servidor inclusive nas imagens. Existe limite de tentativas no login público e na recuperação, e limite de análises por usuário. O login administrativo também limita tentativas; operação comercial ainda exige monitoramento e avaliação de carga. Cookies são somente de sessão e CSRF; não há rastreamento, publicidade ou analytics.
As imagens anotadas ficam no banco, protegidas por login. Faça backup de `local.sqlite3` no uso local; em produção, configure backup no provedor PostgreSQL. Esta versão não tem política automática de retenção, verificação de e-mail, CAPTCHA, quotas de armazenamento por usuário ou monitoramento operacional. Não foi auditada para uso comercial.

## APS
Tema atendido tecnicamente: processamento digital de imagens com Python, principalmente OpenCV, em imagens e vídeos. A entrega acadêmica ainda exige redação, bibliografia, ficha de cada integrante e vídeo público de 5 a 10 minutos. Não invente resultados: apresente também a colher não detectada e o caso das frutas, colete capturas próprias e meça erros antes de afirmar precisão.

## Referências e licenças
- OpenCV Zoo YOLOX: https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_yolox — Apache 2.0; licença em models/LICENSE. Decodificação adaptada deste projeto.
- Artigo: https://arxiv.org/abs/2107.08430
- Segmentação HSV: https://docs.opencv.org/4.x/da/d97/tutorial_threshold_inRange.html
- Django: https://docs.djangoproject.com/en/5.2/
- Imagem café: scikit-image v0.21.0, `skimage/data/coffee.png`; veja exemplos/CREDITOS.txt.
- Imagem frutas: https://github.com/opencv/opencv/blob/master/samples/data/fruits.jpg, somente referência de teste.
