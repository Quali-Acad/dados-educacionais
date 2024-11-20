from guia_da_faculdade import run_scrapper
from estado import Estado

if __name__ == "__main__":
    run_scrapper(2023, 2023, Estado, output_file="dados_academicos.csv")