import csv
import time

import requests
from bs4 import BeautifulSoup as soup
from fake_useragent import UserAgent


class GuiaFaculdade:
    def __init__(self) -> None:
        pass

def run_guia_faculdade():
	list_state_url = __get_list_state_url()

	list_csv_content = []

	ano = ""

	for state_url in list_state_url:
		try:
			ano = __get_year(state_url)
		except Exception as ignored:
			ano = "Não encontrado"

		page_soup = soup(requests.get(state_url, headers={'User-Agent': __get_random_user_agent()}, stream=True).content, "html.parser")

		infos_page_soup = page_soup.find_all('p')

		texto = []

		for info in infos_page_soup:
			texto.append(info.text)

		__clean_unused_info(texto)

		texto_out = __get_texto_out(texto)

		avaliacao = page_soup.find_all("div", {"class": "box-estrelas"})

		notas = __get_notas(avaliacao)

		list_csv_content = __get_list_csv_content(texto_out, notas, ano)

	__write_csv(list_csv_content)

	print("Finalizado!")


def __get_list_state_url() -> list:
	list_state_url = []

	# 27
	br_states = ["Acre", "Alagoas", "Amapa", "Amazonas", "Bahia", "Ceara", "Distrito+Federal", "Espirito+Santo", "Goias", "Maranhao", "Mato+Grosso", "Mato+Grosso+do+Sul", "Minas+Gerais", "Para",
			"Paraiba", "Parana", "Pernambuco", "Piaui", "Rio+de+Janeiro", "Rio+Grande+do+Norte", "Rio+Grande+do+Sul", "Rondonia", "Roraima", "Santa+Catarina", "Sao+Paulo", "Sergipe", "Tocantins"]

	# Formata URL's, gerando dinamicamente com todos os estados brasileiros entre os anos de 2018 e 2022 (pois de 2018 pra tras os dados sao iguais).
	cont_ano = 18

	# na url, 18 = 2018, 22 = 2022
	while cont_ano <= 22: 
		for state in br_states:
			state_url = 'https://publicacoes.estadao.com.br/guia-da-faculdade/page/1/?post_type=faculdades_20' + \
					str(cont_ano) + '&ano=20' + str(cont_ano) + '&s=' + state + \
					'&tipo=&modalidade=&estado=&cidade=&classificacao='
			
			page_soup = soup(requests.get(state_url, headers={'User-Agent': __get_random_user_agent()}, stream=True).content, "html.parser")

			try:
				page_number = page_soup.find("a", attrs={"class": "page-numbers"})

				next_page_number = int(page_number.next)

				for page in range(1, next_page_number + 1): # todo + 2?
					# Adiciona as URL's de 2020
					state_url = "https://publicacoes.estadao.com.br/guia-da-faculdade/page/" + str(page) + "/?post_type=faculdades_20" + \
							str(cont_ano) + "&ano=20" + str(cont_ano) + "&s=" + state + "&tipo=&modalidade=&estado=&cidade=&classificacao="
					
					list_state_url.append(state_url)
			except Exception as ignored:
				list_state_url.append(state_url)

		cont_ano = cont_ano + 1

	return list_state_url


def __get_random_user_agent():
    ua = UserAgent()
    return ua.firefox


def __get_year(state_url: str) -> str:
	'''
		# todo ainda travaremos 2018 - 2022? 

		if "2018" in url:
			ano = "2018"
		elif "2019" in url:
			ano = "2019"
		elif "2020" in url:
			ano = "2020"
		elif "2021" in url:
			ano = "2021"
		elif "2022" in url:
			ano = "2022"
		else:
			ano = "Não encontrado"
	'''	

	return state_url.split("&ano=")[1].split("&s=")[0]


def __get_texto_out(texto: list) -> list:
	texto_in = []
	texto_out = []

	cont = 1
	presencial = False

	for t in texto:
		texto_in.append(t)

		if t == 'Modalidade : Presencial' or 'Rua:' in t:
			presencial = True
		elif t == 'Modalidade : EaD': # Nessa os campos de endereco nao existem
			presencial = False

		if cont >= 14 and presencial:
			cont = 0
			texto_out.append(texto_in)
			texto_in = []
		elif cont >= 11 and not presencial:
			cont = 0
			texto_out.append(texto_in)
			texto_in = []

		cont = cont + 1

	return texto_out


def __get_notas(avaliacao: list) -> list:
	notas = []

	for nota in avaliacao:
		if nota.text == "\nNão Estrelado\n" or nota.text == "\nSem notas\n" or nota.text == "\nNão avaliado\n":
			notas.append("N/A")
		elif nota.text == "\n\n\n\n\n\n":  # Avaliacao: Excelente (5 estrelas)
			notas.append("5")
		elif nota.text == "\n\n\n\n\n":  # Avaliacao: Muito Bom (4 estrelas)
			notas.append("4")
		elif nota.text == "\n\n\n\n":  # Avaliacao: Bom (3 estrelas)
			notas.append("3")

	return notas


def __get_list_csv_content(texto_out: list, notas: list, ano: str) -> list:
	list_csv_content = []
	
	cont = 0

	for e in texto_out:
		# Curso
		texto_out[cont][0] = e[0]

		ies = str(e[2])
		ies = ies.replace("IES: ", "")
		texto_out[cont][1] = ies

		try:
			modalidade = str(e[4])
			modalidade = modalidade.split()
			texto_out[cont][2] = modalidade[2]

		except:
			if 'Rua:' in str(e[10]):
				texto_out[cont][2] = "Presencial"
			else:
				texto_out[cont][2] = "EaD"

		verbete = str(e[5])
		verbete = verbete.replace("Verbete: ", "")
		texto_out[cont][3] = verbete

		titulacao = str(e[6])
		titulacao = titulacao.split()
		texto_out[cont][4] = titulacao[1]

		campus = str(e[7])
		campus = campus.replace("Campus: ", "")
		texto_out[cont][5] = campus

		categoria = str(e[8])
		categoria = categoria.replace("Categoria: ", "")
		texto_out[cont][6] = categoria

		duracao = str(e[9])
		duracao = duracao.replace("Duração: ", "")
		texto_out[cont][7] = duracao

		# Endereco
		if texto_out[cont][2] == "EaD":
			texto_out[cont][8] = ""  # -> Endereco
			texto_out[cont][9] = ""  # -> Cidade
			texto_out[cont][10] = ""  # -> Estado
		else:
			texto_out[cont][8] = str(e[10])  # -> Endereco
			texto_out[cont][9] = str(e[11]).replace("Cidade:  ", "")  # -> Cidade
			texto_out[cont][10] = str(e[12]).replace("Estado: ", "")  # -> Estado

		site = str(e[len(e) - 1])
		site = site.replace("Site: ", "")

		# Avaliacao
		try:
			texto_out[cont][11] = site
			texto_out[cont][12] = notas[cont]
			texto_out[cont][13] = ano

		except:
			texto_out[cont].append(site)
			texto_out[cont].append(notas[cont])
			texto_out[cont].append(ano)

		cont = cont + 1

	list_csv_content.append(texto_out)

	return list_csv_content


def __clean_unused_info(texto: list) -> None:
	# 7 primeiras linhas
    del texto[:7]

    # 5 ultimas linhas
    del texto[-5:]


def __write_csv(list_csv_content: list, chunk_size: int = 8192) -> None:
    header = ["Curso", "IES", "Modalidade", "Verbete", "Titulação", "Campus", "Categoria",
                "Duracao", "Endereco", "Cidade", "Estado", "Site", "Avaliação", "Ano da Avaliação"]

    with open(f"guia_da_faculdade_definitivo_{int(time.time())}.csv" , 'w', encoding='utf-8') as f:
        writer = csv.writer(f)

        writer.writerow(header)

        for chunk_start in range(0, len(list_csv_content), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(list_csv_content))

            chunk = list_csv_content[chunk_start:chunk_end]

            for csv_content in chunk:
                for row in csv_content:
                    writer.writerow(row)
