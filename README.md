# ConfereVision — versão 2

Conferência visual de kits em Python, Django e OpenCV, com usuários, administração, detecção real YOLOX, imagens, vídeos e histórico privado.

## Situação desta entrega
Aplicação implementada e testada localmente. Código versionado em repositório privado: https://github.com/oenzoalmeida/ConfereVision. Publicação no Render ainda NÃO realizada: é necessário conectar o repositório no painel e informar DATABASE_URL (PostgreSQL persistente) e ADMIN_PASSWORD. Não é um produto comercial validado nem substitui os documentos acadêmicos exigidos pela APS.

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

## Hospedagem gratuita preparada
Arquivos `render.yaml` e `build.sh` descrevem um serviço Python Free no Render. Não há recursos pagos no manifesto. O serviço requer PostgreSQL externo persistente via DATABASE_URL; não use o SQLite local para hospedagem gratuita no Render, pois o disco é efêmero. O aplicativo bloqueia inicialização em produção sem DATABASE_URL e SECRET_KEY.

Antes do deploy:
1. Disponibilizar este código em repositório GitHub novo, sem banco e credenciais. Os arquivos grandes de modelo ficam fora do git; o build baixa e verifica o modelo.
2. Escolher o workspace correto no Render. Os disponíveis nesta sessão são QueueFlow e PenteFino; nenhum foi selecionado automaticamente.
3. Conectar um PostgreSQL persistente em plano gratuito compatível. O PostgreSQL gratuito do próprio Render expira em 30 dias; não é a configuração sugerida para guardar o projeto.
4. Criar o Blueprint Free e informar DATABASE_URL, ADMIN_PASSWORD e demais variáveis solicitadas. Não publique segredos no GitHub.
5. Conferir HTTPS, `/healthz`, cadastro, acesso administrativo e uma análise real após publicar.

O Render Free hiberna após 15 minutos sem tráfego e pode levar cerca de um minuto para voltar. As franquias são compartilhadas por workspace. Consulte limites de consumo e cobrança da conta antes de ativar: https://render.com/docs/free. Não foi alterado plano nem criado recurso nesta entrega.

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
