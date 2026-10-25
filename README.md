# extrator-sumulas-tribunais

[![CI](https://github.com/jadefigueredo/extrator-sumulas-tribunais/actions/workflows/ci.yml/badge.svg)](https://github.com/jadefigueredo/extrator-sumulas-tribunais/actions/workflows/ci.yml)

> Collects *súmulas* (binding case-law summaries) published as PDFs by Brazilian courts and turns them into structured JSON.

Coleta as súmulas que os tribunais publicam em PDF, extrai o texto e transforma cada uma em um registro estruturado: número, enunciado, resolução, publicação, datas e referências.

| Tribunal | Fonte | Cobertura |
| --- | --- | --- |
| `tjpa` — Tribunal de Justiça do Pará | [Súmulas do TJPA](https://www.tjpa.jus.br/PortalExterno/institucional/Acordaos-e-Jurisprudencia/1042-Sumulas.xhtml) | todas as súmulas listadas nas quatro páginas |
| `tre-pa` — Tribunal Regional Eleitoral do Pará | [Súmulas do TRE-PA](https://www.tre-pa.jus.br/jurisprudencia/sumulas-tre-pa-1/sumulas-tre-pa) | súmulas 5 em diante (as de 1 a 4 são páginas HTML, não PDFs) |

## Como rodar

Com Docker, sem instalar nada além dele. Primeiro crie um `.env` com os IDs do seu
usuário, para o container gravar em `data/` com a sua permissão (e não como root):

```bash
printf 'UID=%s\nGID=%s\n' "$(id -u)" "$(id -g)" > .env
docker compose up --build                 # todos os tribunais
docker compose run --rm extrator tre-pa   # só o TRE-PA
```

Os arquivos `data/tjpa.json` e `data/tre-pa.json` aparecem na pasta do projeto.

Ou com Python 3.11+:

```bash
pip install .
sumulas                 # todos os tribunais, saída em ./data
sumulas tjpa -o saida   # só o TJPA, em ./saida
```

## Saída

```json
{
  "tribunal": "tjpa",
  "total": 32,
  "sumulas": [
    {
      "tribunal": "tjpa",
      "numero": 7,
      "enunciado": "Não padece do vício de inconstitucionalidade o disposto no art. 310, inciso II, do CPP, com redação dada pela Lei n° 12.403/2011.",
      "url_fonte": "https://www.tjpa.jus.br/CMSPortal/VisualizarArquivo?idArquivo=...",
      "resolucao": "Res. 020/2012",
      "publicacao": "DJ. N° 5131/2012, 16/10/2012",
      "data_publicacao": "2012-10-16",
      "data_aprovacao": null,
      "referencias": []
    }
  ],
  "falhas": []
}
```

Documentos que falham no download ou na conversão vão para `falhas` sem interromper os demais. O comando termina com código 1 se algum tribunal não render nenhuma súmula, o que facilita usá-lo num agendador. O workflow [Coleta](.github/workflows/coleta.yml) faz isso toda segunda-feira e publica os JSONs como artefato; também dá para disparar manualmente na aba Actions.

## Como funciona

```
página de listagem ──► links dos PDFs ──► download ──► texto (pdfplumber) ──► parser do tribunal ──► JSON
```

- **Download** (`http.py`): `httpx` em HTTP/2 com headers de navegador — o WAF de alguns tribunais (ex.: Akamai no TRE-PA) responde 403 a clientes HTTP/1.1 ou sem cara de navegador. Tem limite de concorrência, timeout e retry com backoff exponencial e jitter para erros transitórios (timeouts, 429, 5xx); erros 4xx não são repetidos.
- **Conversão** (`pdf.py`): `pdfplumber`, sem serviços externos. O pipeline recebe o conversor como parâmetro, então dá para trocar de biblioteca sem mexer nos parsers.
- **Extração** (`tribunais/`): cada tribunal sabe onde estão seus PDFs e como ler um documento. O texto é achatado numa linha só e lido por marcadores textuais (`Referências:`, `Publicada no`, `Data de Aprovação`), porque a quebra de linha que sai de um PDF não é confiável.

### Adicionando um tribunal

1. Crie `src/sumulas/tribunais/<sigla>.py` com uma subclasse de `Tribunal` que implemente `find_links` e `parse`.
2. Registre-a em `src/sumulas/tribunais/__init__.py`.
3. Salve o texto de alguns documentos em `tests/fixtures/<sigla>/` e escreva os testes do parser.

## Testes

```bash
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
```

Ou `docker compose --profile test run --rm tests`.

Os testes rodam sem rede: os parsers usam textos de súmulas reais salvos em `tests/fixtures/`, o cliente HTTP é testado contra um servidor local que simula falhas, e um teste gera um PDF na hora para passar pelo `pdfplumber` de ponta a ponta. O CI roda tudo em Python 3.11, 3.12 e 3.13 e também faz o build da imagem Docker.

## Contribuindo

Os commits seguem [Conventional Commits](https://www.conventionalcommits.org/pt-br/): `feat:`, `fix:`, `test:`, `docs:`, `chore:`.

## Licença

[MIT](LICENSE)
