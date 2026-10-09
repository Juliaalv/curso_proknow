# Curso ProKnow-C com Python — plano de trabalho

Documento de planejamento para desenvolver, no Claude Code, o material de um curso de 4 horas sobre a metodologia ProKnow-C com automações em Python.

## 1. Contexto

- **O que é**: curso de 4 horas sobre ProKnow-C (Knowledge Development Process – Constructivist), ministrado por Julia Alves.
- **Público**: pesquisadores e estudantes que vão fazer revisão de literatura. Não se assume que saibam programar.
- **Restrição central**: o curso **não ensina programação**. O Python aparece como ferramenta pronta: o participante preenche campos e executa.
- **Material existente**: slides antigos cobrindo apenas a etapa de seleção do portfólio bibliográfico (problemática, definição, eixos e palavras-chave, bases, teste de aderência, filtragem, ferramentas). Exemplo usado nos slides: previsão de velocidade do vento (eixos "Wind Speed" e "Forecasting").
- **Código existente**: nenhum a reaproveitar; as automações serão desenvolvidas do zero neste repositório.
- **Premissa sobre as bases**: assume-se que os participantes **não conhecem as bases de dados científicas**. O curso apresenta todas as principais e suas características (seção 3.4). Os participantes são alunos da universidade e têm acesso ao Portal de Periódicos CAPES, portanto às bases assinadas.
- **Tema da prática**: um tema comum para toda a turma, **curtailment de eólica e solar** (eixos: curtailment, fontes renováveis, soluções/mitigação e aspectos econômicos).
- **Bases da prática**: **Scopus e IEEE Xplore**, no máximo. A instrutora demonstra ao vivo a busca e a exportação; em seguida, cada aluno entra manualmente nas duas bases (via Portal CAPES), faz a busca, baixa os CSVs e os coloca na pasta de entrada do curso, com uma subpasta por base (seção 8.1). A A2 lê e concatena tudo o que estiver nessa pasta. Como são duas bases com colunas e convenções diferentes, padronizar e tratar esses arquivos continua sendo parte obrigatória do fluxo, não um detalhe.
- **Reserva**: o material traz os CSVs brutos exportados pela instrutora, na mesma estrutura de pastas, para quem não conseguir acessar as bases na aula.
- **Objetivo adicional**: ir além do ProKnow-C clássico, trazendo técnicas que tornem a revisão mais profunda.

### 1.1 Objetivos de aprendizagem

Ao final do curso, o participante será capaz de:

1. Explicar as quatro etapas do ProKnow-C e o fluxo de filtragem da seleção do portfólio.
2. Diferenciar os tipos de ferramenta (base indexadora, plataforma de editora, portal de acesso, buscador) e escolher bases adequadas ao próprio tema.
3. Montar uma string de busca com eixos, operadores booleanos e curingas.
4. Exportar resultados de uma base e padronizá-los, junto com os de outra base, em uma tabela única.
5. Executar os notebooks do curso para filtrar um portfólio, gerar a análise bibliométrica e o fluxograma de contagens.
6. Reaplicar os notebooks, depois do curso, ao próprio tema de pesquisa.

### 1.2 Pré-requisitos do participante

- Computador com navegador e conta Google (para usar o Colab e o Google Drive).
- Login institucional (CAFe) funcionando, testado antes da aula, para acessar a Scopus e a IEEE Xplore pelo Portal CAPES.

## 2. O que precisa ser produzido

1. Notebooks (Google Colab) com as automações, usáveis sem ler código, cada um executável de forma independente (seção 8).
2. Um conjunto de dados de exemplo do tema curtailment de eólica e solar: os CSVs brutos exportados da Scopus e da IEEE Xplore (com seus defeitos), organizados na mesma estrutura da pasta de entrada, e o resultado salvo de cada etapa, para que cada notebook possa começar do ponto certo.
3. Slides atualizados (esquema de cores azul), alinhados ao cronograma abaixo.
4. Um guia curto para o participante (como abrir, preencher, executar e salvar resultados), incluindo o passo a passo ilustrado de acesso e exportação na Scopus e na IEEE Xplore e de como colocar os CSVs na pasta de entrada.

Pronto significa:
- **Em aula**: o participante, sem experiência em programação, exporta os próprios CSVs do tema comum e percorre o fluxo completo, de "dois eixos e suas palavras-chave" até um portfólio filtrado, com gráficos bibliométricos e um fluxograma de contagens, apenas preenchendo formulários. As leituras de título, resumo e texto completo não cabem no tempo do curso: a triagem é demonstrada em poucos artigos e, a partir daí, o fluxo segue com as tabelas do exemplo, que já trazem as decisões preenchidas.
- **Depois da aula**: o participante consegue repetir o fluxo com o próprio tema, a partir das próprias exportações.

## 3. Referência do método

### 3.1 As quatro etapas do ProKnow-C

1. Seleção do portfólio bibliográfico.
2. Análise bibliométrica.
3. Análise sistêmica (leitura crítica por "lentes" para identificar lacunas).
4. Definição da pergunta de pesquisa e dos objetivos.

### 3.2 Seleção do portfólio

1. Definição dos eixos de pesquisa e das palavras-chave.
2. Definição das bases de dados e dos critérios de busca (campos título/resumo/palavras-chave, recorte temporal).
3. Teste de aderência das palavras-chave: selecionar 2 artigos cujo título sugira adequação e verificar se suas palavras-chave estão contempladas na busca. Se não, reajustar e buscar de novo.
4. Filtragem do banco de artigos brutos.

### 3.3 Fluxo de filtragem

1. Remoção de registros incompletos e de duplicados.
2. Alinhamento pelo título.
3. Reconhecimento científico: ordenar por citações e aplicar um corte sobre o percentual acumulado (a literatura costuma usar algo em torno de 80 a 85%; o valor é escolha do pesquisador).
   - **Acima do corte**: leitura do resumo → grupo A (reconhecidos e alinhados).
   - **Abaixo do corte e recentes**: leitura do resumo (repescagem dos recentes).
   - **Abaixo do corte e antigos**: só vão para a leitura do resumo se algum autor estiver no banco de autores do grupo A. Os aprovados nessa leitura se juntam ao portfólio.
   - **Recente** = publicado há menos de 2 anos em relação ao ano da pesquisa (ex.: pesquisa feita em 2026 → artigos de 2025 e 2026).
4. Disponibilidade do texto integral.
5. Alinhamento pelo texto completo.
6. Teste de representatividade: analisar as referências do portfólio e incorporar as mais citadas que estejam alinhadas (base complementar). É o último passo da seleção; no curso, abre o bloco de bibliometria (A9), porque usa as mesmas referências.

**Fonte de citações**: a literatura do ProKnow-C usa tradicionalmente o Google Scholar. O curso usa o OpenAlex como fonte única, por ser aberto e reprodutível. Apresentar isso nos slides como escolha da instrutora, não como regra do método.

### 3.4 Bases de dados a apresentar

Os participantes não conhecem as bases, então o bloco "Bases e busca" começa do zero. Todas as ferramentas da tabela são apresentadas; a prática usa só Scopus e IEEE Xplore.

**Primeiro, a diferença entre os tipos de ferramenta** (fonte comum de confusão):

- **Base indexadora**: reúne registros (título, resumo, citações) de periódicos de muitas editoras. Ex.: Scopus, Web of Science.
- **Plataforma de editora**: dá acesso ao texto completo do que aquela editora publica. Ex.: ScienceDirect (Elsevier), IEEE Xplore (IEEE).
- **Portal de acesso**: não é uma base; é a porta de entrada para as bases assinadas. Ex.: Portal de Periódicos CAPES.
- **Buscador acadêmico**: cobertura ampla, pouco controle sobre a busca. Ex.: Google Scholar.

**Bases e ferramentas**

| Ferramenta | Tipo | Cobertura | Acesso | Exportação | Ponto de atenção |
|---|---|---|---|---|---|
| Scopus | Indexadora (Elsevier) | Multidisciplinar, muito ampla | Assinatura, via Portal CAPES | CSV, RIS, BibTeX | Boa primeira escolha; traz citações e referências |
| Web of Science | Indexadora (Clarivate) | Multidisciplinar, mais seletiva | Assinatura, via Portal CAPES | Texto tabulado, Excel, RIS, BibTeX (em lotes) | Origem do fator de impacto (JCR); não exporta CSV |
| IEEE Xplore | Plataforma de editora | Engenharia elétrica, eletrônica, computação | Assinatura, via Portal CAPES | CSV | Muito artigo de congresso; filtrar por tipo de documento; CSV sem referências |
| ScienceDirect | Plataforma de editora | Apenas conteúdo da Elsevier | Assinatura, via Portal CAPES | RIS, BibTeX | Não confundir com a Scopus; boa parte já está indexada nela |
| Portal de Periódicos CAPES | Portal de acesso | Reúne as bases assinadas | Login institucional (CAFe) | — | É por onde se entra nas bases pagas, dentro ou fora da universidade |
| DOAJ | Diretório | Periódicos de acesso aberto | Gratuito | Limitada | Sem contagem de citações |
| SciELO | Biblioteca de acesso aberto | América Latina, muito conteúdo em português | Gratuito | RIS, BibTeX, CSV | Útil quando a literatura nacional importa |
| Google Scholar | Buscador | A mais ampla, inclui teses e preprints | Gratuito | Sem exportação em massa | Busca pouco reprodutível; útil para conferir citações e achar PDFs |
| OpenAlex | Catálogo aberto | Multidisciplinar, muito ampla | Gratuito | CSV e API | Usado nas automações para citações e referências |

Os detalhes de exportação mudam com o tempo; conferir cada um antes do curso.

**O que mostrar para todas as bases**: o que é, cobertura, como se acessa, que formatos exporta e o ponto de atenção (a tabela acima, um slide por base principal).

**O que mostrar em detalhe para Scopus e IEEE Xplore** (bases da prática)
- Como entrar pelo Portal CAPES com login institucional (CAFe).
- Onde colar a string de busca e como restringir a título, resumo e palavras-chave.
- Como aplicar o recorte de anos e de tipo de documento.
- Como exportar: que formato escolher e quais campos marcar (incluir resumo, palavras-chave, citações e referências).

**Como orientar a escolha de duas bases** (para a pesquisa própria, depois do curso)
- Par mais comum: Scopus + Web of Science (ampla + seletiva).
- Para temas de engenharia elétrica e computação: acrescentar ou trocar uma delas pela IEEE Xplore (por isso a prática usa Scopus + IEEE Xplore).
- Evitar o par Scopus + ScienceDirect, pela grande sobreposição.
- Sem acesso institucional: OpenAlex + SciELO ou DOAJ.

**Demonstração ao vivo**: fazer a busca do exemplo (curtailment de eólica e solar) na Scopus e na IEEE Xplore, exportar os dois CSVs e abri-los lado a lado para mostrar que as colunas não batem. Esse contraste é a motivação para a automação A2.

**Atividade**: cada aluno repete a busca nas duas bases, baixa os CSVs, coloca cada um na subpasta da sua base (seção 8.1) e roda a A2. Quem não conseguir acessar usa os CSVs de reserva.

### 3.5 Ajustes conceituais a fazer nos slides

- "Somente artigos em inglês", "sem teses e congressos" e "últimos 10 anos" são **delimitações do pesquisador**, não regras do método. Apresentar assim.
- Incluir o corte de citações (item 3 acima), hoje ausente, com a repescagem completa (antigos voltam à leitura do resumo).
- Incluir o teste de representatividade (item 6), hoje ausente, como último passo da seleção.
- Explicar a escolha do OpenAlex como fonte de citações.
- Mostrar as quatro etapas do método, mesmo que o curso aprofunde só a primeira e a segunda.
- Substituir o slide atual de logotipos das bases por slides que as apresentem de fato (seção 3.4): tipos de ferramenta, um slide por base principal e um slide de como escolher o par.

## 4. Cronograma (240 min)

| Horário | Min | Bloco | Conteúdo | Automação demonstrada |
|---|---|---|---|---|
| 0:00–0:15 | 15 | Abertura | Problemática; revisão narrativa x sistemática; onde o ProKnow-C se encaixa | — |
| 0:15–0:40 | 25 | Eixos e palavras-chave | As 4 etapas; eixos, operadores booleanos, curingas. Atividade: montar os eixos e a string do tema comum | A1 |
| 0:40–1:25 | 45 | Bases e busca | Tipos de ferramenta; visão geral de todas as bases (seção 3.4); demonstração ao vivo na Scopus e na IEEE Xplore; por que os arquivos não são compatíveis. Atividade: cada aluno exporta os CSVs, coloca-os na pasta de entrada e executa a A2 | A2 |
| 1:25–1:50 | 25 | Aderência e filtragem I | Teste de aderência, duplicados, alinhamento de título (triagem demonstrada em poucos artigos) | A3, A4, A5 |
| 1:50–2:05 | 15 | Intervalo | | |
| 2:05–2:45 | 40 | Filtragem II | Reconhecimento científico, resumo, repescagem, disponibilidade, texto completo | A6, A7, A8 |
| 2:45–3:20 | 35 | Representatividade e bibliometria | Teste de representatividade (fecha a seleção); periódicos, autores, palavras-chave e anos | A9 |
| 3:20–3:45 | 25 | Além do ProKnow-C | Snowballing, InOrdinatio, síntese com LLM | B1, B2, B4 (demos curtas) |
| 3:45–4:00 | 15 | Fechamento | Fluxograma e checklist PRISMA; ferramentas (Zotero, Mendeley); entrega dos notebooks; dúvidas | A10 |

Demonstração ao vivo prioritária: A1, A2, A4, A5 (curta), A6, A9 e A10. As demais e o B3 entram como material extra se o tempo apertar.

## 5. Automações do núcleo ProKnow-C

Todas operam sobre uma tabela única de artigos (seção 7). Cada notebook é independente: começa carregando a tabela da etapa anterior (a do exemplo ou a salva pelo participante) e termina salvando a sua (seção 8).

### A1 — Gerador de string de busca
- **Entrada**: eixos e listas de palavras-chave; opção de curinga.
- **Saída**: string booleana (OR dentro do eixo, AND entre eixos) na sintaxe de cada base: Scopus (`TITLE-ABS-KEY(...)`), Web of Science (`TS=(...)`), IEEE Xplore, e forma genérica.
- **Notas**: aspas automáticas em termos compostos; aviso sobre termos muito amplos (ex.: "Wind" sozinho).

### A2 — Leitura, padronização e tratamento dos arquivos das bases

Automação central do curso: transforma dois ou mais arquivos heterogêneos em uma única tabela confiável.

**Entrada**: a pasta de entrada (seção 8.1), com uma subpasta por base. Na prática, os CSVs que o aluno baixou da Scopus e da IEEE Xplore (ou os de reserva). Para uso posterior, aceita também texto tabulado/Excel (Web of Science) e RIS, cada um na sua subpasta. Uma mesma base pode ter vários arquivos na subpasta, quando a exportação é feita em lotes ou em buscas separadas.

**Saída**: tabela padronizada e concatenada (esquema da seção 7), mais um relatório de qualidade por arquivo.

**Etapa 1 — Leitura e concatenação**
- Percorrer a pasta de entrada: a subpasta diz de qual base é cada arquivo, e todos os arquivos dela são lidos.
- Detectar codificação (UTF-8 com ou sem BOM, Latin-1) e separador (vírgula, ponto e vírgula, tabulação).
- Conferir o cabeçalho de cada arquivo contra o perfil da base. Se não bater (ex.: CSV da IEEE colocado na pasta da Scopus), avisar qual arquivo está na pasta errada e não lê-lo.
- Concatenar os arquivos de cada base e, depois de padronizados (etapa 2), concatenar as bases em uma tabela única.
- Mostrar um resumo antes de seguir: arquivos encontrados por base, linhas de cada um e arquivos ignorados (pasta vazia, formato não suportado, cabeçalho incompatível).

**Etapa 2 — Mapeamento de colunas (um perfil por base)**

Cada base tem um perfil que traduz suas colunas para o esquema comum. Perfis prontos e testados com exportações reais: **Scopus e IEEE Xplore** (usados na prática). Perfis adicionais, para uso posterior: **Web of Science** e **RIS genérico**. Exemplos de cabeçalhos a conferir antes do curso:

| Campo comum | Scopus (CSV) | Web of Science (tabulado/Excel) | IEEE Xplore (CSV) |
|---|---|---|---|
| `titulo` | Title | TI / Article Title | Document Title |
| `autores` | Authors | AU / Authors | Authors |
| `ano` | Year | PY / Publication Year | Publication Year |
| `periodico` | Source title | SO / Source Title | Publication Title |
| `doi` | DOI | DI / DOI | DOI |
| `resumo` | Abstract | AB / Abstract | Abstract |
| `palavras_chave` | Author Keywords, Index Keywords | DE, ID | Author Keywords, IEEE Terms |
| `citacoes` | Cited by | TC / Times Cited | Article Citation Count |
| `tipo_documento` | Document Type | DT / Document Type | Document Identifier |
| `idioma` | Language of Original Document | LA / Language | — |
| `referencias_texto` | References | CR / Cited References | — |

- Perfis ficam em arquivos de configuração (YAML ou dicionário), para acrescentar uma base sem mexer no código.
- Para base sem perfil, a orientação é exportar em **RIS**, formato que quase todas as bases oferecem (ScienceDirect, SciELO e outras), e colocar o arquivo na subpasta `ris/`, que o perfil RIS genérico lê.

**Etapa 3 — Tratamento**
- `doi`: minúsculas, sem prefixo de URL e sem espaços; DOI inválido vira vazio.
- `titulo`: remover marcações HTML, espaços duplicados e ponto final; guardar também uma versão normalizada (minúsculas, sem acentos e pontuação) para comparação.
- `autores`: converter para lista, unificando separadores e a ordem "Sobrenome, Iniciais".
- `ano` e `citacoes`: converter para inteiro; valores não numéricos viram vazio.
- `palavras_chave`: lista em minúsculas, sem duplicatas, juntando palavras do autor e indexadas (mantendo a origem).
- `resumo`: tratar marcadores de ausência (ex.: "[No abstract available]") como vazio.
- `tipo_documento` e `idioma`: converter para vocabulário único (artigo, revisão, conferência, capítulo, outro; códigos de idioma).
- Registrar `base_origem` e `arquivo_origem` em toda linha.

**Etapa 4 — Aplicação das delimitações**
- Filtros opcionais, definidos pelo participante em formulário: tipo de documento, idioma, intervalo de anos.
- Registros sem título, ou sem ano e DOI, saem como "informação ausente" (filtragem preliminar).
- Cada exclusão fica registrada com o motivo, para o fluxograma de A10.

**Etapa 5 — Relatório de qualidade**
- Por arquivo: linhas lidas, linhas aproveitadas, percentual de campos vazios por coluna.
- Entre bases: quantos registros cada base trouxe e quantos são exclusivos de cada uma (tabela ou diagrama de sobreposição, calculado após A4).
- Avisos legíveis para leigos (ex.: "38% dos registros da base X vieram sem resumo").

**Notas**
- Contagens de citações diferem entre bases para o mesmo artigo. Guardar o valor de cada base em `citacoes_por_base` e não misturar: o corte de A6 usa uma fonte única para todos os artigos.
- API (OpenAlex) fica como complemento, não como caminho principal (ver seção 8).

### A3 — Teste de aderência
- **Entrada**: tabela bruta e 2 ou mais artigos-semente escolhidos pelo participante.
- **Saída**: palavras-chave dos artigos-semente, marcadas como "contemplada" ou "ausente" na busca; sugestão de termos a incluir.
- **Notas**: refazer a busca não cabe na aula; no exemplo, mostrar o resultado do teste e comentar como a string seria reajustada.

### A4 — Deduplicação
- **Entrada**: tabela bruta.
- **Saída**: tabela sem duplicados e relatório do que foi removido.
- **Notas**: primeiro por DOI normalizado; depois por similaridade de título (rapidfuzz) com limiar ajustável, conferindo ano e primeiro autor. Como há sempre duas bases, a maior parte dos duplicados vem da sobreposição entre elas: em vez de descartar, **fundir** os registros, mantendo o mais completo, preenchendo campos vazios com os da outra base (resumo, palavras-chave, referências) e anotando todas as bases em que o artigo apareceu.

### A5 — Triagem assistida (título e resumo)
- **Entrada**: tabela deduplicada.
- **Saída**: coluna de decisão (aceito/rejeitado) e motivo opcional, salvos no Google Drive a cada clique.
- **Notas**: interface com ipywidgets, um artigo por vez. Opcional: ordenar por similaridade semântica com a descrição do tema, para priorizar a leitura. A ferramenta **não decide**; a decisão é do pesquisador (é o que torna o método construtivista). No exemplo, as decisões já vêm preenchidas; em aula, demonstrar a interface em poucos artigos.

### A6 — Reconhecimento científico
- **Entrada**: artigos com título alinhado.
- **Saída**: citações atualizadas, curva de citações acumuladas, corte ajustável por controle deslizante, divisão em "acima do corte" e "abaixo do corte".
- **Notas**: mostrar no gráfico quantos artigos entram em cada valor de corte. Citações vêm de uma única fonte, o OpenAlex (consulta pelo DOI), já que os valores das bases não são comparáveis entre si. No exemplo, as citações já consultadas vêm na tabela de entrada, com `citacoes_data`.

### A7 — Repescagem
- **Entrada**: grupo abaixo do corte e grupo A.
- **Saída**: recentes enviados à leitura de resumo; antigos enviados à leitura de resumo só se houver autor no banco de autores do grupo A.
- **Notas**: "recente" conforme a seção 3.3, com o ano da pesquisa preenchido em formulário. Casar autores pelo nome normalizado ("Sobrenome, Iniciais"); identificadores de autor não são comparáveis entre bases.

### A8 — Disponibilidade
- **Entrada**: lista de DOIs.
- **Saída**: indicação de acesso aberto e link do PDF quando existir (Unpaywall).
- **Notas**: artigos fechados ficam marcados para busca via Portal de Periódicos CAPES.

### A9 — Representatividade e análise bibliométrica
- **Entrada**: portfólio final.
- **Parte 1 — Teste de representatividade** (último passo da seleção): obter as referências de cada artigo do portfólio pelo OpenAlex (`referenced_works`, consultado pelo DOI), listar as mais citadas pelo portfólio e marcar as alinhadas como grupo "complementar".
- **Parte 2 — Bibliometria**: gráficos de periódicos, autores, ano de publicação e palavras-chave mais frequentes.
- **Notas**: O texto das referências exportado pelas bases fica em `referencias_texto` só como registro; não é usado para casar referências.

### A10 — Rastreabilidade e relato PRISMA
- **Entrada**: histórico das etapas.
- **Saída**: fluxograma com a contagem de artigos em cada filtro, começando pelo número de registros por base (formato compatível com o PRISMA 2020); checklist PRISMA resumido; log das decisões; exportação do portfólio em RIS/BibTeX para Zotero ou Mendeley.

## 6. Extensões além do ProKnow-C

### B1 — Snowballing
Busca automática, pelo OpenAlex, das referências do portfólio (para trás) e dos artigos que o citam (para frente). Recupera trabalhos que as palavras-chave não capturaram. Os candidatos passam pelos mesmos filtros de título e resumo.

### B2 — InOrdinatio (Methodi Ordinatio)
Ranking alternativo ao corte por citações, que tende a penalizar artigos recentes:

`InOrdinatio = (FI / 1000) + α × [10 − (ano da pesquisa − ano de publicação)] + citações`

com α entre 1 e 10 conforme o peso dado à atualidade. Mostrar lado a lado o portfólio pelo corte do ProKnow-C e pelo InOrdinatio. Referência: Pagani, Kovaleski e Resende (2015).

O fator de impacto (JCR) não vem nas exportações e nem todos têm acesso a ele. O participante escolhe um substituto em formulário (SJR, CiteScore ou a métrica de citação média de dois anos do OpenAlex), e o slide deixa claro que é uma adaptação da fórmula original.

### B3 — Mapa de subtemas (material extra)
Clusterização dos resumos para revelar as frentes de pesquisa do tema. Versão leve com TF-IDF + KMeans; versão mais rica com embeddings (sentence-transformers) ou BERTopic. Saída: grupos nomeados pelos termos mais característicos e sua evolução por ano. Resultado pré-calculado para o exemplo.

### B4 — Matriz de síntese com LLM
Extração estruturada, a partir do resumo ou do texto completo, de: objetivo, método, dados utilizados, métricas, resultados e lacunas declaradas. Saída em tabela, com conferência humana obrigatória. Dá suporte concreto à análise sistêmica (etapa 3 do método).

Na demonstração, usar resultado pré-calculado, sem chave nem custo durante a aula. Para o participante, entregar também um prompt pronto que pode ser usado em qualquer chat de LLM gratuito, artigo por artigo.

## 7. Esquema da tabela de artigos (proposta)

| Coluna | Descrição |
|---|---|
| `id` | Identificador interno |
| `doi` | DOI normalizado (minúsculas, sem prefixo de URL) |
| `titulo`, `resumo` | Texto |
| `autores`, `autores_ids` | Listas |
| `ano` | Ano de publicação |
| `periodico`, `issn` | Fonte |
| `tipo_documento` | Artigo, conferência, revisão etc. |
| `idioma` | Idioma |
| `palavras_chave` | Lista (do autor e indexadas) |
| `palavras_chave_autor`, `palavras_chave_indexadas` | As mesmas listas separadas por origem (a A3 usa as do autor) |
| `titulo_norm` | Título normalizado para comparação |
| `citacoes`, `citacoes_fonte`, `citacoes_data` | Contagem usada no corte, sua fonte e data |
| `citacoes_por_base` | Contagem informada por cada base |
| `referencias` | Lista de IDs do OpenAlex citados pelo artigo (`referenced_works`) |
| `referencias_texto` | Referências em texto livre, como vieram da base |
| `bases_origem` | Lista das bases em que o artigo apareceu |
| `arquivos_origem` | Arquivos de onde vieram os registros fundidos |
| `acesso_aberto`, `url_pdf` | Disponibilidade |
| `etapa_atual` | Último filtro pelo qual passou |
| `decisao_titulo`, `decisao_resumo`, `decisao_texto` | Aceito/rejeitado em cada leitura |
| `motivo_exclusao` | Texto livre ou categoria |
| `grupo` | A, B, repescagem, complementar |

Armazenamento em Parquet, com exportação em CSV para quem quiser abrir em planilha.

## 8. Formato de entrega e restrições

- **Notebooks no Google Colab** com campos de formulário (`#@param`) e código oculto.
- **Cada notebook é independente**, com a mesma estrutura:
  1. **Preparação**: instala as dependências e o pacote do curso a partir do repositório.
  2. **Entrada**: o participante escolhe, em formulário, entre "usar o exemplo do curso" (carrega a tabela da etapa anterior, já salva no repositório) ou "usar meus arquivos". No notebook 02, "meus arquivos" são os CSVs da pasta `entrada/`; nos demais, é a tabela salva em `resultados/` pelo notebook anterior.
  3. **Execução** da etapa.
  4. **Salvamento**: grava o resultado em `resultados/` na pasta do curso no Google Drive (seção 8.1) e oferece o download. Isso é necessário porque os arquivos da sessão do Colab são apagados quando ela desconecta.
- O notebook da A5 salva cada decisão no Drive no momento do clique, para não se perder a triagem se a sessão cair.

### 8.1 Pasta do curso no Google Drive

Criada automaticamente na primeira execução de qualquer notebook (montando o Drive):

```
Meu Drive/
└── curso_proknowc/
    ├── entrada/          # o aluno coloca aqui os arquivos baixados das bases
    │   ├── scopus/       # um ou mais CSVs exportados da Scopus
    │   ├── ieee/         # um ou mais CSVs exportados da IEEE Xplore
    │   ├── wos/          # (uso posterior) texto tabulado ou Excel da Web of Science
    │   └── ris/          # (uso posterior) arquivos RIS de qualquer outra base
    └── resultados/       # tabelas salvas ao fim de cada notebook
```

- O aluno coloca os arquivos pelo próprio Google Drive (arrastando para a subpasta) ou pelo painel de arquivos do Colab. O guia mostra os dois caminhos.
- No notebook 02, a célula de entrada lista o que encontrou em cada subpasta. Se a pasta estiver vazia, mostra uma mensagem dizendo onde colocar os arquivos e pede para rodar a célula de novo.
- Não é preciso renomear os arquivos: vale o nome que a base deu. O que importa é a subpasta.
- A opção "usar o exemplo do curso" lê os CSVs de reserva do repositório, na mesma estrutura.
- **Sem dependência de chave individual**: a API do Scopus exige chave e acesso institucional por pessoa, o que não funciona para uma turma. Caminho principal: os CSVs exportados da Scopus e da IEEE Xplore. Complemento por API: OpenAlex e Unpaywall (abertos; conferir limites e exigências atuais, como necessidade de chave, antes do curso).
- **Tempo de execução**: cada célula demonstrada ao vivo deve rodar em poucos segundos no conjunto de exemplo. Modelos pesados (embeddings, BERTopic) e a síntese com LLM têm resultado pré-calculado.
- **Idioma**: interface, mensagens e gráficos em português.
- **Transparência**: toda etapa automática mostra o que removeu e por quê; nenhuma decisão de alinhamento é tomada pela ferramenta sem o pesquisador.

Bibliotecas previstas: pandas, pyarrow, openpyxl, charset-normalizer, pyyaml, rapidfuzz, rispy, requests (ou pyalex), matplotlib/plotly, ipywidgets, scikit-learn; opcionais: sentence-transformers, bertopic.

## 9. Estrutura de repositório (proposta)

O repositório precisa ser público (GitHub), porque os notebooks baixam dele o pacote e os dados de exemplo.

```
curso-proknowc/
├── README.md
├── PLANO.md                  # este documento
├── notebooks/
│   ├── 01_string_de_busca.ipynb                       # A1
│   ├── 02_leitura_padronizacao.ipynb                  # A2
│   ├── 03_aderencia_dedup_triagem.ipynb               # A3, A4, A5
│   ├── 04_reconhecimento_repescagem_disponibilidade.ipynb  # A6, A7, A8
│   ├── 05_representatividade_bibliometria.ipynb       # A9
│   ├── 06_rastreabilidade_prisma.ipynb                # A10
│   ├── 07_alem_do_proknowc.ipynb                      # B1 a B4
│   └── 00_fluxo_completo.ipynb
├── src/curso_proknowc/       # funções chamadas pelos notebooks
│   └── perfis/               # scopus, ieee, wos, ris
├── dados/
│   ├── exemplo_bruto/        # CSVs de reserva, mesma estrutura da pasta entrada/: scopus/, ieee/
│   └── exemplo_processado/   # tabela salva ao fim de cada etapa (entrada do notebook seguinte)
├── slides/
└── guia_participante.md
```

## 10. Ordem de desenvolvimento sugerida

1. Exportar da Scopus e da IEEE Xplore os CSVs reais do tema curtailment de eólica e solar.
2. Esquema da tabela, perfis Scopus e IEEE Xplore e leitura da pasta de entrada, concatenação, padronização e tratamento (A2), testados com esses CSVs (incluindo mais de um arquivo por base e um arquivo na pasta errada). É a base de todo o resto.
3. A4 com fusão entre bases e relatório de sobreposição; depois A1 e A6.
4. A9 e A10: fecham o fluxo com representatividade, gráficos e fluxograma.
5. A3, A5, A7 e A8.
6. Estrutura comum dos notebooks (preparação, entrada, salvamento no Drive) e geração das tabelas de cada etapa em `dados/exemplo_processado/`.
7. Extensões B1 e B2 (baratas de implementar depois que a coleta existe); B4 e B3 com resultados pré-calculados.
8. Perfis Web of Science e RIS genérico.
9. Notebook de fluxo completo, guia do participante e slides.
10. Ensaio cronometrado com o conjunto de exemplo, em uma conta Colab limpa, conferindo também: regras de acesso atuais do OpenAlex e do Unpaywall e salvamento no Drive.

## 11. Decisões em aberto

- Número de participantes e se usarão computador próprio.
- Se a exportação é feita na aula (como está no cronograma) ou como tarefa prévia. Na aula, o login CAFe de toda a turma ao mesmo tempo é um risco; os CSVs de reserva cobrem quem não conseguir.
- Qual LLM usar para pré-calcular o B4.
- Valor padrão do corte de citações a apresentar (sugestão: 80%, mostrando no controle deslizante como o portfólio muda).
- Onde hospedar o repositório público (conta pessoal ou institucional).

## 12. Referências

- Vilela, L. O. (2012). Aplicação do ProKnow-C para seleção de um portfólio bibliográfico e análise bibliométrica sobre avaliação de desempenho da gestão do conhecimento. *Revista Gestão Industrial*, 8(1). https://doi.org/10.3895/s1808-04482012000100005
- Ensslin, L., Ensslin, S. R., Lacerda, R. T. O., Tasca, J. E. (2010). ProKnow-C, Knowledge Development Process – Constructivist. Processo técnico com patente de registro pendente junto ao INPI.
- Pagani, R. N., Kovaleski, J. L., Resende, L. M. (2015). Methodi Ordinatio: a proposed methodology to select and rank relevant scientific papers encompassing the impact factor, number of citation, and year of publication. *Scientometrics*, 105.
- Page, M. J. et al. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. *BMJ*, 372.
