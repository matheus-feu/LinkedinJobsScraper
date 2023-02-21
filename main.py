from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs4
from loguru import logger
import pandas as pd
import time


class LinkedinJobsScraper():
    def __init__(self, base_url, job_role, country):
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.driver.maximize_window()
        self.base_url = base_url
        self.job_role = job_role
        self.country = country
        self.df = None

        logger.info("Iniciando o Scraper do Linkedin Jobs")

    def get_jobs(self):
        """Get all jobs from the page"""
        logger.info(f"Abrindo a URL: {self.base_url}")
        self.driver.get(self.base_url)
        time.sleep(2)

        xpath_job_role = '/html/body/div[1]/header/nav/section/section[2]/form/section[1]/input'

        box_job_role = self.driver.find_element(By.XPATH, xpath_job_role)
        box_job_role.send_keys(self.job_role)
        logger.info(f"Buscando vagas para o cargo: {self.job_role}")
        time.sleep(2)

        xpath_clear = '/html/body/div[1]/header/nav/section/section[2]/form/section[2]/button'
        logger.info("Apagando campo de busca de países")
        self.driver.find_element(By.XPATH, xpath_clear).click()

        xpath_countries = '/html/body/div[1]/header/nav/section/section[2]/form/section[2]/input'
        box_countries = self.driver.find_element(By.XPATH, xpath_countries)
        logger.info(f"Buscando vagas para o país: {self.country}")
        box_countries.send_keys(self.country)
        time.sleep(5)

        xpath_select_country = '//*[@id="location-1"]'
        logger.info(f"Selecionando o país: {self.country} desejado para a busca")
        self.driver.find_element(By.XPATH, xpath_select_country).click()
        time.sleep(5)

        height_initial = self.driver.execute_script('return document.body.scrollHeight')
        logger.info("Rolando a página para baixo")

        while True:
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(3)

            height_final = self.driver.execute_script('return document.body.scrollHeight')

            try:
                self.driver.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/button').click()
                logger.info("Clicando no botão de carregar mais vagas")
                time.sleep(3)

                self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')

                height_final = self.driver.execute_script('return document.body.scrollHeight')
            except:
                pass

            if height_initial < height_final:
                height_initial = height_final
            else:
                break

        soup = bs4(self.driver.page_source, 'lxml')
        logger.info("Extraindo as informações das vagas")

        all_jobs = soup.find('ul', {'class': 'jobs-search__results-list'})
        box_jobs = all_jobs.find_all('li')
        logger.info("Criando o DataFrame com as informações das vagas")

        self.df = pd.DataFrame(columns=[
            'Link da Vaga',
            'Link da Empresa',
            'Cargo',
            'Nome da Empresa',
            'Local',
            'Tempo de Abertura',
            'Status da Vaga'
        ])

        for job in box_jobs:
            try:
                link = job.find('a',
                                {'class': 'base-card__full-link absolute top-0 right-0 bottom-0 left-0 p-0 z-[2]'}).get(
                    'href')
            except:
                link = job.find('a', {
                    'class': 'base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card'}).get(
                    'href')

            try:
                linkedin_empresa = job.find('a', {'class': 'hidden-nested-link'}).get('href')
            except:
                linkedin_empresa = job.find('a', {
                    'class': 'base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card'}).get(
                    'href')
            try:
                cargo = job.find('span', {'class': 'sr-only'}).text.strip()
            except:
                cargo = job.find('h3', {'class': 'base-search-card__title'}).text.strip()

            try:
                nome_empresa = job.find('a', {'class': 'hidden-nested-link'}).text.strip()
            except:
                nome_empresa = job.find('h4', {'class': 'base-search-card__subtitle'}).text.strip()

            local = job.find('span', {'class': 'job-search-card__location'}).text.strip()

            try:
                tempo = job.find('time', {'class': 'job-search-card__listdate'}).text.strip()
            except:
                tempo = job.find('time', {'class': 'job-search-card__listdate--new'}).text.strip()

            try:
                status = job.find('span', {'class': 'result-benefits__text'}).text.strip()
            except:
                status = ' '

            self.df.loc[len(self.df)] = [
                link,
                linkedin_empresa,
                cargo,
                nome_empresa,
                local,
                tempo,
                status
            ]

            self.df.head()

            self.df.to_excel('vagas.xlsx', index=False)
            logger.info("Salvando o DataFrame em um arquivo CSV")


if __name__ == '__main__':
    base_url = 'https://www.linkedin.com/jobs/search/?currentJobId=3474245390'
    job_role = 'Desenvolvedor Python'
    country = 'Brasil'
    scraper = LinkedinJobsScraper(base_url, job_role, country)
    scraper.get_jobs()
