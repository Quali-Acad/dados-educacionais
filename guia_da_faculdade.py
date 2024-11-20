import re
from typing import Iterable, Any, Optional, Type

import pandas as pd
import requests
from bs4 import BeautifulSoup as soup
from pydantic import BaseModel, Field, ConfigDict
from tqdm.auto import tqdm
from estado import Estado

class CardData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ies: str = Field(alias="IES")
    nome: str = Field(alias="NOME/CURSO")
    modalidade: str = Field(alias="MODALIDADE")
    verbete: str = Field(alias="VERBETE")
    titulacao: str = Field(alias="TITULAÇÃO")
    campus: str = Field(alias="CAMPUS")
    categoria: str = Field(alias="CATEGORIA")
    duracao: str = Field(alias="DURAÇÃO")
    endereco: Optional[str] = Field(None, alias="ENDEREÇO")
    site: str = Field(alias="SITE")
    telefone: Optional[str] = Field(None, alias="TELEFONE")
    avaliacao: int = Field(alias="AVALIAÇÃO")
    cidade: Optional[str] = Field(None, alias="CIDADE")
    estado: Optional[str] = Field(None, alias="ESTADO")
    ano_avaliação: int = Field(alias="ANO DE AVALIAÇÃO")

def run_scrapper(start_year: int, end_year: int, estados: Type[Estado], *, output_file: str):
    df = pd.DataFrame()

    for estado in tqdm(list(estados), desc="Estados"):
        for year in range(start_year, end_year + 1):
            print(f"\nProcessando {estado.value} - Ano {year}")
            page = get_page_by_year(year, estado.value)
            total_pages = get_page_count(page)

            with tqdm(total=total_pages, desc="Páginas") as pbar:
                while True:
                    cards_iter = process_page(page, year)
                    page_records = []

                    for card in cards_iter:
                        page_records.append(card.model_dump(by_alias=True))

                    if page_records:
                        df = pd.concat([df, pd.DataFrame(page_records)], ignore_index=True)

                    pbar.update(1)

                    next_page_link = get_next_page_link(page)
                    if not next_page_link:
                        break

                    page = get_page_from_url(next_page_link)

    df.to_csv(output_file, index=False)
    print("Concluído!")

def get_page_by_year(year: int, estado: str = '') -> soup:

    base_url = "https://publicacoes.estadao.com.br/guia-da-faculdade/"

    params = {
        "post_type": f"faculdades_{year}",
        "ano": str(year),
        "estado": str(estado),
    }

    return get_page_from_url(base_url, **params)

def get_page_from_url(url: str, params: dict) -> soup:
    result = requests.get(url, params=params)
    return soup(result.content, "html.parser")

def get_page_count(page: soup) -> int:
    page_numbers = page.find_all(["a", "span"], class_="page-numbers")
    if not page_numbers:
        return 1
    try:
        return int(page_numbers[-2].text)
    except (IndexError, ValueError):
        return 1

def get_next_page_link(page: soup) -> Optional[str]:
    link = page.find("a", class_="next page-numbers")
    if link:
        return link.get("href")
    return None

def process_page(page: soup, year: int) -> Iterable[CardData]:
    cards_list = page.find_all("div", class_="box-listagem")
    for card in cards_list:
        yield process_card(card, year)


def process_card(card: soup, year: int) -> CardData:
    header = card.find("div", class_="box-basico")
    body = card.find("div", class_="box-completo")
    data: dict[str, Any] = {"ano_avaliação": year}

    # body
    field_order = [
        "ies",
        "nome",
        "modalidade",
        "verbete",
        "titulacao",
        "campus",
        "categoria",
        "duracao",
        "site",
        "telefone",
    ]

    if "ead" not in body.text.lower():
        field_order.insert(8, "endereco")

    space_regex = re.compile(" +")
    comma_regex = re.compile(", *,")

    for field, p_elem in zip(field_order, body.find_all("p")):  # type: ignore
        p_elem.find("span").decompose()
        content = p_elem.text.strip().replace("\n", " ")
        content = space_regex.sub(" ", content)
        content = comma_regex.sub(",", content)
        data[field] = content

    # header
    data["avaliacao"] = len(header.find_all("img", class_="estrela"))  # type: ignore

    if data["modalidade"].lower() != "ead":
        cidade, uf = header.find_all("p")[1].text.rsplit("|", maxsplit=1)[-1].rsplit("-", maxsplit=1)  # type: ignore
        data["cidade"] = cidade.strip()
        data["estado"] = uf.strip()

    return CardData.model_validate(data)
