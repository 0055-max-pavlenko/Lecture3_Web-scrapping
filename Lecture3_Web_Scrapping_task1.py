from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

import requests
import json
from fake_headers import Headers
from bs4 import BeautifulSoup
from datetime import datetime


headers = Headers(browser = 'chrome', os = 'win')


#Данные по вакансиям «python» в Москве и Санкт-Петербурге за сутки
#Применяем Selenium тк requests возвращает только 20 вакансий со страницы вместо 50 
service = Service(executable_path= ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.get('https://hh.ru/search/vacancy?area=1&area=2&ored_clusters=true&text=python&search_period=1')
html_data = driver.page_source.encode('utf-8')


#Определяем общее количество страниц с вакансиями
number_pages = []
pages_list = BeautifulSoup(html_data, 'lxml')
tag_pages = pages_list.find_all('span', class_ = "pager-item-not-in-short-range")
for item in tag_pages:
    number_pages.append(item.find('span').text)

#Проходимся по всем страницам и выбираем вакансии у которых в описании есть ключевые слова "Django" и "Flask"
count = 1
parsed_data = []


for page in range(int(number_pages[-1])):
    driver.get(f'https://hh.ru/search/vacancy?area=1&area=2&ored_clusters=true&text=python&search_period=1&page={page}')
    job_list_html_data = driver.page_source.encode('utf-8')
    jobs_list = BeautifulSoup(job_list_html_data, 'lxml')
    tag_jobs = jobs_list.find_all('div', class_ = "serp-item")
        
    for job in tag_jobs:
        #Собираем со страницы вакансий данные по вакансии
        vacancy_title = job.find('a', class_ = "serp-item__title").text
        vacancy_link = job.find('a', class_ = "serp-item__title")['href']
        try:
            vacancy_salary = job.find('span', attrs={'data-qa': 'vacancy-serp__vacancy-compensation'}).text
        except:
            vacancy_salary = 'з/п не указана'
        try:
            employer_name = job.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'}).text
            employer_link = 'https://hh.ru' + job.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-employer'})['href']
        except:
            employer_name = 'Работадатель не указан'
            employer_link = 'Ссылка на сайт работадателя не указана'
        try:
            employer_city = job.find('div', attrs={'data-qa': 'vacancy-serp__vacancy-address'}).text
        except:
            employer_city = 'Город работы не указан'
        
        job_description_html_data = requests.get(f"{job.find('a')['href']}", headers = headers.generate()).text
        job_description = BeautifulSoup(job_description_html_data, 'lxml')
        
        #Есть страницы с описанием вакансии с нестандартной структурой html - их не читаем
        try: 
            job_description_text = job_description.find('div', class_='vacancy-description').text
        except:
            job_description_text = 'не удалось получить'
        
        # Если в описании вакансии есть слова 'Django' и 'Flask' добавляем запись в список 
        if 'Django' in job_description_text and 'Flask' in job_description_text:
            parsed_data.append(
                {
                   'Порядковый номер записи': count,
                   'Название позиции' : vacancy_title,
                   'Ссылка на описание позиции' : vacancy_link,
                   'Данные по зарплате' : vacancy_salary,
                   'Название работадателя' : employer_name,
                   'Ссылка на сайт работадателя' : employer_link,
                   'Город работадателя' : employer_city
                    
                    })
            count +=1
            print(count)
    
        

#Записываем все данные в файл
with open(f'{datetime.now().strftime("%d_%m_%y-%H_%M")}.json','w', encoding = 'utf-8') as file:
    json.dump(parsed_data, file, indent = 3, ensure_ascii = False)
    