"""Gera os notebooks do curso (notebooks/*.ipynb) com a mesma estrutura (seção 8 do plano).

Uso: python ferramentas/gerar_notebooks.py

Cada célula de código vira um formulário do Colab: o código fica oculto e o aluno só vê os campos.
"""

from datetime import date
from pathlib import Path

import nbformat

REPOSITORIO = "https://github.com/Juliaalv/curso_proknow.git"

PASTA = Path(__file__).resolve().parents[1] / "notebooks"
ANO = date.today().year


def texto(conteudo: str):
    return nbformat.v4.new_markdown_cell(conteudo.strip())


def formulario(titulo: str, codigo: str):
    celula = nbformat.v4.new_code_cell(f'#@title {titulo} {{ display-mode: "form" }}\n{codigo.strip()}')
    celula.metadata["cellView"] = "form"
    return celula


def preparacao(com_drive: bool = True):
    codigo = f'''
REPOSITORIO = "{REPOSITORIO}"
import os, subprocess, sys
if "google.colab" in sys.modules:
    if not os.path.exists("/content/curso_proknowc"):
        subprocess.run(["git", "clone", "-q", "--depth", "1", REPOSITORIO, "/content/curso_proknowc"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", "/content/curso_proknowc"], check=True)
    sys.path.insert(0, "/content/curso_proknowc/src")
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import HTML, display
from curso_proknowc import colab
'''
    if com_drive:
        codigo += '''
pastas = colab.preparar()
print("Tudo pronto. Pasta do curso:", pastas.raiz)
'''
    else:
        codigo += 'print("Tudo pronto.")\n'
    return formulario("Preparação (rode esta célula primeiro)", codigo)


def entrada(nome: str, notebook: str, variavel: str, padrao: str = "exemplo do curso", email: bool = False):
    campo_email = '\nEMAIL = "" #@param {type:"string"}' if email else ""
    nota_email = (
        "\n#@markdown **EMAIL**: o seu e-mail, usado nas consultas ao OpenAlex e ao Unpaywall (o Unpaywall exige)."
        if email
        else ""
    )
    return formulario(
        "Entrada",
        f'''
#@markdown **exemplo do curso**: começa do resultado já pronto do exemplo (curtailment de eólica e solar).
#@markdown **meus arquivos**: começa do resultado que você salvou no notebook anterior.{nota_email}
FONTE = "{padrao}" #@param ["exemplo do curso", "meus arquivos"]{campo_email}
{variavel} = colab.carregar(pastas, FONTE, "{nome}", notebook="{notebook}")
print(f"{{len({variavel})}} artigos carregados.")
''',
    )


CAMPOS_EIXOS = '''
#@markdown Separe os termos de um mesmo eixo com ponto e vírgula. Use * como curinga (ex.: curtail*). Deixe em branco os eixos que não precisar.
EIXO_1 = "Curtailment" #@param {type:"string"}
TERMOS_1 = "curtail*; constrained-off; dispatch-down" #@param {type:"string"}
EIXO_2 = "Fontes renováveis (solar e eólica)" #@param {type:"string"}
TERMOS_2 = "wind power; wind energy; wind farm*; photovoltaic*; solar power; solar energy; variable renewable*" #@param {type:"string"}
EIXO_3 = "Soluções / mitigação" #@param {type:"string"}
TERMOS_3 = "energy storage; battery energy storage system*; BESS; flexibility; demand response; hydrogen production; planned load growth" #@param {type:"string"}
EIXO_4 = "Aspectos econômicos" #@param {type:"string"}
TERMOS_4 = "econom*; cost*; revenue*; electricity market*; techno-economic; compensation; carbon targets" #@param {type:"string"}
eixos = colab.ler_eixos([(EIXO_1, TERMOS_1), (EIXO_2, TERMOS_2), (EIXO_3, TERMOS_3), (EIXO_4, TERMOS_4)])
'''

SALVAR = 'BAIXAR_CSV = False #@param {type:"boolean"}'


def nb01():
    return [
        texto("""
# 1. String de busca (A1)

Defina os eixos da sua pesquisa e as palavras-chave de cada um. O notebook monta a string de busca
(OR dentro de cada eixo, AND entre os eixos) na sintaxe de cada base.

**Como usar:** clique no botão ▶ à esquerda de cada célula, de cima para baixo.
"""),
        preparacao(com_drive=False),
        formulario("Eixos e palavras-chave", CAMPOS_EIXOS + '''
MANTER_CURINGA = True #@param {type:"boolean"}
from curso_proknowc.string_busca import avisos, gerar_strings
strings = gerar_strings(eixos, MANTER_CURINGA)
for chave, rotulo in [("scopus", "Scopus"), ("web_of_science", "Web of Science"), ("ieee", "IEEE Xplore"), ("generica", "Forma genérica")]:
    print(f"{rotulo}:\\n{strings[chave]}\\n")
for aviso in avisos(eixos):
    print("Atenção:", aviso)
'''),
        texto("""
Copie a string da base e cole no campo de busca avançada dela. No passo seguinte (notebook 2),
você vai exportar os resultados em CSV e colocá-los na sua pasta do Google Drive.
"""),
    ]


def nb02():
    return [
        texto("""
# 2. Leitura e padronização dos arquivos das bases (A2)

Junta os CSVs exportados da Scopus e da IEEE Xplore em uma tabela única e padronizada.

**Antes de rodar:** depois da célula de preparação, abra o Google Drive e coloque os arquivos em
`curso_proknowc/entrada/scopus/` e `curso_proknowc/entrada/ieee/`. Pode haver vários arquivos por base.
Não precisa renomear: o que importa é a pasta.
"""),
        preparacao(),
        formulario("Leitura dos arquivos", '''
#@markdown **meus arquivos**: os CSVs que você colocou em `curso_proknowc/entrada/` no Google Drive.
#@markdown **exemplo do curso**: os CSVs de reserva do curso (tema curtailment de eólica e solar).
FONTE = "meus arquivos" #@param ["meus arquivos", "exemplo do curso"]
from curso_proknowc.leitura import ler_pasta
tabela_bruta, arquivos = ler_pasta(colab.pasta_entrada(pastas, FONTE))
display(arquivos)
if (arquivos["situacao"] == "lido").sum() == 0:
    raise SystemExit(f"Nenhum CSV foi lido. Coloque os arquivos em {pastas.entrada / 'scopus'} e {pastas.entrada / 'ieee'} e rode esta célula de novo.")
print(f"{len(tabela_bruta)} registros lidos e padronizados.")
'''),
        formulario("Delimitações (opcional)", '''
#@markdown Deixe 0 ou em branco para não aplicar o filtro. Tipos: artigo; revisão; conferência; capítulo; outro. Idiomas: en; pt; es (registros sem idioma informado são mantidos).
ANO_INICIAL = 0 #@param {type:"integer"}
ANO_FINAL = 0 #@param {type:"integer"}
TIPOS = "" #@param {type:"string"}
IDIOMAS = "" #@param {type:"string"}
from curso_proknowc import rastreabilidade
from curso_proknowc.delimitacoes import aplicar_delimitacoes, remover_incompletos
lista = lambda campo: [t.strip() for t in campo.split(";") if t.strip()]
completos, incompletos = remover_incompletos(tabela_bruta)
anos = (ANO_INICIAL or 0, ANO_FINAL or 9999) if (ANO_INICIAL or ANO_FINAL) else None
padronizada, fora = aplicar_delimitacoes(completos, anos=anos, tipos=lista(TIPOS), idiomas=lista(IDIOMAS))
colab.registrar_bases(pastas, rastreabilidade.registros_por_base(tabela_bruta))
colab.registrar_etapa(pastas, "02", "Registros incompletos", len(tabela_bruta), incompletos)
colab.registrar_etapa(pastas, "02", "Delimitações", len(completos), fora)
print(f"Sem informação mínima: {len(incompletos)}. Fora das delimitações: {len(fora)}. Seguem: {len(padronizada)}.")
'''),
        formulario("Relatório de qualidade e salvamento", SALVAR + '''
from curso_proknowc.relatorio import relatorio_qualidade
por_arquivo, avisos = relatorio_qualidade(padronizada, pd.concat([incompletos, fora]), arquivos)
display(por_arquivo)
for aviso in avisos:
    print("•", aviso)
colab.salvar(pastas, padronizada, "02_padronizado", baixar=BAIXAR_CSV)
print(f"\\n{len(padronizada)} registros salvos em {pastas.resultados}.")
'''),
    ]


def nb03():
    return [
        texto("""
# 3. Aderência, duplicados e triagem pelo título (A3, A4, A5)
"""),
        preparacao(),
        entrada("02_padronizado", "03", "padronizada"),
        formulario("Artigos disponíveis (para escolher os artigos-semente)", '''
display(padronizada[["id", "titulo", "ano", "base_origem"]].head(30))
'''),
        texto("""
## Teste de aderência (A3)

Escolha pelo menos 2 artigos cujo título indique que são do seu tema. O teste confere se as
palavras-chave deles estão contempladas pelos termos da sua busca.
"""),
        formulario("Teste de aderência", CAMPOS_EIXOS + '''
#@markdown Artigos-semente: ids (ex.: R00001) ou trechos do título, separados por ponto e vírgula.
SEMENTES = "" #@param {type:"string"}
from curso_proknowc.aderencia import sementes_da_tabela, testar_aderencia
escolhas = [s.strip() for s in SEMENTES.split(";") if s.strip()]
if len(escolhas) < 2:
    print("Informe pelo menos 2 artigos-semente (id ou trecho do título) para rodar o teste.")
else:
    tabela_aderencia, sugestoes, mensagem = testar_aderencia(eixos, sementes_da_tabela(padronizada, escolhas))
    display(tabela_aderencia)
    print(mensagem)
    if sugestoes:
        print("Sugestões:", "; ".join(sugestoes))
'''),
        texto("## Duplicados (A4)\n\nO mesmo artigo costuma vir das duas bases. Os registros repetidos são fundidos, completando um com o outro."),
        formulario("Remoção de duplicados", '''
#@markdown Semelhança mínima entre títulos para considerar duplicado (os artigos também precisam ter ano e primeiro autor compatíveis).
LIMIAR = 90 #@param {type:"slider", min:80, max:100, step:1}
from curso_proknowc.deduplicacao import deduplicar, sobreposicao
sem_duplicados, fundidos = deduplicar(padronizada, LIMIAR)
duplicados = padronizada[padronizada["id"].isin(fundidos["id_removido"])].assign(motivo_exclusao="duplicado")
colab.registrar_etapa(pastas, "03", "Duplicados", len(padronizada), duplicados)
print(f"{len(fundidos)} duplicado(s) fundido(s). Seguem {len(sem_duplicados)} artigos.")
display(fundidos)
print("Sobreposição entre as bases:")
display(sobreposicao(sem_duplicados))
'''),
        texto("""
## Triagem pelo título (A5)

Leia cada título e decida se ele está alinhado ao seu tema. **Quem decide é você.**
Cada clique é salvo na hora no seu Google Drive; se a sessão cair, rode de novo e a triagem continua de onde parou.
Com o exemplo do curso, quase todas as decisões já vêm preenchidas.
"""),
        formulario("Triagem pelo título", '''
#@markdown Opcional: descreva o tema para ver primeiro os artigos mais parecidos com ele. A ordem não decide nada.
DESCRICAO_DO_TEMA = "" #@param {type:"string"}
from curso_proknowc import triagem
decisoes = colab.arquivo_decisoes(pastas, FONTE)
fila = triagem.ordenar_por_similaridade(sem_duplicados, DESCRICAO_DO_TEMA) if DESCRICAO_DO_TEMA.strip() else sem_duplicados
display(triagem.interface(fila, "titulo", decisoes))
'''),
        formulario("Aplicar as decisões e salvar (rode depois de terminar a triagem)", SALVAR + '''
try:
    alinhados, nao_alinhados = colab.aplicar_triagem(sem_duplicados, "titulo", decisoes)
except ValueError as erro:
    print(erro)
else:
    colab.registrar_etapa(pastas, "03", "Alinhamento pelo título", len(sem_duplicados), nao_alinhados)
    colab.salvar(pastas, alinhados, "03_alinhados_titulo", baixar=BAIXAR_CSV)
    print(f"Alinhados pelo título: {len(alinhados)}. Não alinhados: {len(nao_alinhados)}. Resultado salvo.")
'''),
    ]


def nb04():
    return [
        texto("""
# 4. Reconhecimento científico, repescagem, disponibilidade e leituras (A6, A7, A8)

Sequência do ProKnow-C: corte por citações → leitura do resumo dos mais citados (grupo A) →
repescagem → leitura do resumo dos repescados → disponibilidade → leitura do texto completo.
"""),
        preparacao(),
        entrada("03_alinhados_titulo", "04", "alinhados", email=True),
        texto("## Reconhecimento científico (A6)\n\nAs citações vêm de uma fonte única, o OpenAlex, para que os números sejam comparáveis entre si."),
        formulario("Citações", '''
#@markdown Consulta o OpenAlex (precisa de internet). O exemplo do curso já vem com as citações consultadas.
ATUALIZAR_CITACOES = True #@param {type:"boolean"}
from curso_proknowc import reconhecimento
if ATUALIZAR_CITACOES:
    alinhados, avisos = reconhecimento.atualizar_citacoes(alinhados, email=EMAIL or None)
    for aviso in avisos:
        print("•", aviso)
print("Quantos artigos ficam acima de cada corte:")
display(reconhecimento.artigos_por_corte(alinhados))
'''),
        formulario("Corte por citações", '''
#@markdown Percentual das citações acumuladas a partir do qual os artigos ficam "abaixo do corte". A escolha é sua (a literatura costuma usar de 80 a 85%).
CORTE = 80 #@param {type:"slider", min:50, max:95, step:5}
reconhecimento.grafico_curva(alinhados, CORTE)
plt.show()
acima, abaixo = reconhecimento.dividir_por_corte(alinhados, CORTE)
acima = acima.assign(grupo="A")
print(f"Acima do corte: {len(acima)} artigos. Abaixo do corte: {len(abaixo)}.")
'''),
        formulario("Leitura do resumo: artigos acima do corte", '''
from curso_proknowc import triagem
decisoes = colab.arquivo_decisoes(pastas, FONTE)
display(triagem.interface(acima, "resumo", decisoes))
'''),
        texto("## Repescagem (A7)\n\nRode depois de terminar a leitura acima. Recentes voltam para a leitura do resumo; os antigos só voltam se tiverem um autor do grupo A."),
        formulario("Repescagem", f'''
ANO_DA_PESQUISA = {ANO} #@param {{type:"integer"}}
from curso_proknowc import repescagem
try:
    grupo_a, _ = colab.aplicar_triagem(acima, "resumo", decisoes)
except ValueError as erro:
    raise SystemExit(f"{{erro}} (leitura do resumo dos artigos acima do corte)")
enviados, descartados = repescagem.repescar(abaixo, grupo_a, ANO_DA_PESQUISA)
colab.registrar_etapa(pastas, "04", "Reconhecimento científico e repescagem", len(alinhados), descartados)
print(f"Grupo A: {{len(grupo_a)}} artigos. Repescados para a leitura do resumo: {{len(enviados)}}. Excluídos: {{len(descartados)}}.")
print("Autores do grupo A (banco de autores):")
display(repescagem.banco_autores(grupo_a).head(15))
if len(enviados):
    display(enviados[["id", "titulo", "ano", "motivo_repescagem"]])
else:
    print("Nenhum artigo abaixo do corte foi repescado: a próxima leitura pode ser pulada.")
'''),
        formulario("Leitura do resumo: artigos repescados", '''
display(triagem.interface(enviados, "resumo", decisoes))
'''),
        formulario("Resultado da leitura dos resumos (rode depois de terminar)", '''
para_resumo = pd.concat([acima, enviados], ignore_index=True)
try:
    aprovados, rejeitados = colab.aplicar_triagem(para_resumo, "resumo", decisoes)
except ValueError as erro:
    raise SystemExit(str(erro))
colab.registrar_etapa(pastas, "04", "Leitura do resumo", len(para_resumo), rejeitados)
print(f"Aprovados na leitura do resumo: {len(aprovados)}. Não alinhados: {len(rejeitados)}.")
'''),
        texto("## Disponibilidade do texto completo (A8)\n\nOs artigos fechados ficam marcados para você buscar pelo Portal de Periódicos CAPES."),
        formulario("Disponibilidade", '''
from curso_proknowc.disponibilidade import verificar_disponibilidade
if EMAIL.strip():
    aprovados = verificar_disponibilidade(aprovados, EMAIL.strip())
    display(aprovados[["id", "titulo", "acesso_aberto", "url_pdf", "obs_disponibilidade"]])
else:
    print("Preencha o EMAIL na célula de entrada e rode de novo para consultar o Unpaywall (ele exige um e-mail).")
'''),
        texto("""## Leitura do texto completo

A leitura do texto completo é feita **fora do notebook**: abra cada artigo na base de dados, no site da revista,
pelo link do PDF em acesso aberto ou pelo Portal de Periódicos CAPES (para os fechados). Depois de ler, volte aqui
e registre a decisão. Se não conseguir o texto, rejeite e escreva o motivo (ex.: "texto indisponível")."""),
        formulario("Registro da leitura do texto completo", '''
#@markdown A tela mostra o título e os links de cada artigo; a leitura é feita na base. Aqui você só registra a decisão.
display(triagem.interface(aprovados, "texto", decisoes))
'''),
        formulario("Aplicar as decisões e salvar o portfólio (rode depois de terminar)", SALVAR + '''
try:
    portfolio, rejeitados_texto = colab.aplicar_triagem(aprovados, "texto", decisoes)
except ValueError as erro:
    print(erro)
else:
    colab.registrar_etapa(pastas, "04", "Leitura do texto completo", len(aprovados), rejeitados_texto)
    colab.salvar(pastas, portfolio, "04_portfolio", baixar=BAIXAR_CSV)
    print(f"Portfólio: {len(portfolio)} artigos. Resultado salvo.")
'''),
    ]


def nb05():
    return [
        texto("""
# 5. Representatividade e análise bibliométrica (A9)
"""),
        preparacao(),
        entrada("04_portfolio", "05", "portfolio", email=True),
        texto("""
## Teste de representatividade

Último passo da seleção: as referências mais citadas pelos artigos do portfólio. As que estiverem
alinhadas ao seu tema entram no portfólio como "complementares".
"""),
        formulario("Referências mais citadas pelo portfólio", '''
#@markdown Consulta o OpenAlex (precisa de internet).
BUSCAR_REFERENCIAS = True #@param {type:"boolean"}
QUANTAS = 20 #@param {type:"integer"}
from curso_proknowc import bibliometria
if BUSCAR_REFERENCIAS:
    portfolio, avisos = bibliometria.obter_referencias(portfolio, email=EMAIL or None)
    for aviso in avisos:
        print("•", aviso)
mais_citadas, avisos = bibliometria.referencias_mais_citadas(portfolio, QUANTAS, email=EMAIL or None)
for aviso in avisos:
    print("•", aviso)
if len(mais_citadas):
    display(mais_citadas.drop(columns="alinhada"))
else:
    print("Nenhuma referência encontrada. Marque BUSCAR_REFERENCIAS para consultar as referências no OpenAlex.")
'''),
        formulario("Incorporar as referências alinhadas e salvar", SALVAR + '''
#@markdown Copie da tabela acima os códigos (coluna openalex_id) das referências alinhadas ao seu tema, separados por ponto e vírgula.
ALINHADAS = "" #@param {type:"string"}
marcadas = {c.strip() for c in ALINHADAS.split(";") if c.strip()}
mais_citadas["alinhada"] = mais_citadas["openalex_id"].isin(marcadas)
portfolio_final = bibliometria.incorporar_complementares(portfolio, mais_citadas)
incluidas = len(portfolio_final) - len(portfolio)
colab.registrar_etapa(pastas, "05", "Teste de representatividade", len(portfolio), portfolio.iloc[0:0], incluidos=incluidas)
colab.salvar(pastas, portfolio_final, "05_portfolio_final", baixar=BAIXAR_CSV)
print(f"{incluidas} referência(s) incorporada(s). Portfólio final: {len(portfolio_final)} artigos.")
'''),
        texto("## Análise bibliométrica"),
        formulario("Periódicos, autores, palavras-chave e anos", '''
QUANTOS_NO_GRAFICO = 10 #@param {type:"integer"}
for coluna in ["periodico", "autores", "palavras_chave"]:
    bibliometria.grafico_frequencias(portfolio_final, coluna, QUANTOS_NO_GRAFICO)
    plt.show()
bibliometria.grafico_anos(portfolio_final)
plt.show()
'''),
    ]


def nb06():
    return [
        texto("""
# 6. Rastreabilidade e relato PRISMA (A10)

Fluxograma com a contagem de artigos em cada etapa, registro das exclusões, checklist PRISMA
e exportação do portfólio para o Zotero ou o Mendeley.
"""),
        preparacao(),
        formulario("Entrada", '''
#@markdown **exemplo do curso**: o histórico e o portfólio do exemplo. **meus arquivos**: o que você salvou nos notebooks anteriores.
FONTE = "exemplo do curso" #@param ["exemplo do curso", "meus arquivos"]
portfolio = colab.carregar(pastas, FONTE, "05_portfolio_final", notebook="06")
por_base, etapas, excluidos = colab.historico(pastas, FONTE)
print(f"Portfólio: {len(portfolio)} artigos. Etapas registradas: {len(etapas)}.")
'''),
        formulario("Fluxograma", '''
from curso_proknowc import rastreabilidade
figura = rastreabilidade.fluxograma(etapas, por_base)
figura.savefig(pastas.resultados / "fluxograma.png", dpi=200, bbox_inches="tight")
plt.show()
print(f"Imagem salva em {pastas.resultados / 'fluxograma.png'}.")
'''),
        formulario("Registro das exclusões", '''
log = rastreabilidade.log_decisoes(excluidos)
log.to_csv(pastas.resultados / "log_exclusoes.csv", index=False, encoding="utf-8-sig")
display(log)
'''),
        formulario("Checklist PRISMA", '''
print(rastreabilidade.checklist_prisma(etapas, por_base))
'''),
        formulario("Exportar para o Zotero ou o Mendeley", '''
BAIXAR = False #@param {type:"boolean"}
ris = rastreabilidade.exportar_ris(portfolio, pastas.resultados / "portfolio.ris")
bib = rastreabilidade.exportar_bibtex(portfolio, pastas.resultados / "portfolio.bib")
print(f"Arquivos salvos: {ris.name} e {bib.name}, em {pastas.resultados}.")
if BAIXAR and colab.no_colab():
    from google.colab import files
    files.download(str(ris))
    files.download(str(bib))
'''),
    ]


NOTEBOOKS = {
    "01_string_de_busca": nb01,
    "02_leitura_padronizacao": nb02,
    "03_aderencia_dedup_triagem": nb03,
    "04_reconhecimento_repescagem_disponibilidade": nb04,
    "05_representatividade_bibliometria": nb05,
    "06_rastreabilidade_prisma": nb06,
}


def gerar(pasta: Path = PASTA) -> list:
    pasta.mkdir(parents=True, exist_ok=True)
    caminhos = []
    for nome, construir in NOTEBOOKS.items():
        caderno = nbformat.v4.new_notebook(cells=construir())
        caderno.metadata.update(
            {
                "colab": {"provenance": []},
                "kernelspec": {"name": "python3", "display_name": "Python 3"},
                "language_info": {"name": "python"},
            }
        )
        caminho = pasta / f"{nome}.ipynb"
        nbformat.write(caderno, caminho)
        caminhos.append(caminho)
    return caminhos


if __name__ == "__main__":
    for caminho in gerar():
        print("Gerado:", caminho)
