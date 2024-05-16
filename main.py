from scrapper import run_scrapper
from guia_faculdade import run_guia_faculdade

if __name__ == "__main__":
    run_scrapper(2020, 2023, output_file="dados_academicos.csv")  # todo testar 2018
    #run_guia_faculdade()
    # todo trazer csv pra sql
