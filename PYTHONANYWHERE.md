# Publicação preparada no PythonAnywhere

Situação: configuração criada, mas hospedagem não realizada. É necessário autenticar a conta no provedor para instalar e publicar.

Esta configuração usa o disco persistente da conta e SQLite para a demonstração com um único processo web. Mantém DEBUG desativado, HTTPS, proteção CSRF e isolamento por usuário. Não use esta configuração no disco efêmero do Render.

No servidor, após extrair a pasta e instalar requirements.txt em um ambiente virtual Python 3.12:

    python prepare_pythonanywhere.py

O preparador cria uma chave privada com permissão 600, executa migrações, prepara admin (sem substituir credenciais existentes), reúne arquivos estáticos, verifica segurança e gera pythonanywhere_wsgi.py. Não altera qualquer aplicação de hospedagem existente.

A aplicação web no painel deve apontar ao ambiente virtual e ao conteúdo de pythonanywhere_wsgi.py. O endereço depende do usuário real da conta. Testar login, troca de senha, cadastro e processamento após a publicação.

Plano gratuito: 512 MiB de disco, 1 web worker e vencimento da aplicação após um mês; conferir renovação no painel. A instalação das dependências e a capacidade de processamento precisam ser verificadas na conta antes de confirmar compatibilidade. Use pip --no-cache-dir para evitar ocupar disco com cache. Faça backup do local.sqlite3.

Nunca publique deployment-private.json, local.sqlite3 ou ACESSO_ADMIN.txt em um repositório público.
