import traceback
import pandas as pd

import requests
# Importações a remover abaixo
import logging as logger

from io import StringIO
from time import time
from configparser import ConfigParser
from pandas import DataFrame


class TableProcessor(object):

    def __init__(self, dataframe: DataFrame) -> None:
        self.dataframe = dataframe

    def process(self) -> DataFrame:
        self._drop_columns(columns=['Depoimento'])
        self._standarlize_dates(columns=['Data Início', 'Último Acesso', 'Data Conclusão'])
        self._remove_phone_mask(columns=['Contato'])
        self._from_percentage_to_decimal(columns=['Etapa em curso'])
        self._cut_decimal_values(columns=['Carga Horária do Colaborador'])
        self._fill_empty_columns()
        return self.dataframe

    def _drop_columns(self, columns):
        start_time = time()
        try:
            logger.info('Removendo colunas desnecessárias')
            self.dataframe.drop(columns, inplace=True, axis=1)

            logger.info(
                f'Success : Time = {round(time() - start_time,1)}s : Removed = {columns}')
        except Exception as e:
            logger.error(
                f'Error : Time = {round(time() - start_time,1)}s : Exception = {e}')

    def _standarlize_dates(self, columns):
        start_time = time()
        try:
            logger.info('Padronizando colunas de data')
            invalid_date = ['0000-00-00 00:00:00']
            self.dataframe.replace(to_replace=invalid_date, value=pd.NaT, inplace=True)

            for column in columns:
                self.dataframe[column] = pd.to_datetime(self.dataframe[column], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d/%m/%Y')
            
            logger.info(f'Success : Time = {round(time() - start_time,1)}s')
        except Exception as e:
            logger.error(
                f'Error : Time = {round(time() - start_time,1)}s : Exception = {e}')

    def _remove_phone_mask(self, columns):
        start_time = time()
        try:
            logger.info('Removendo caracteres especiais (args:(,),-) das colunas de contato')
            replace_pattern = {}
            for column in columns:
                replace_pattern[column] = r'[\(\)\-]'
            
            self.dataframe.replace(to_replace=replace_pattern, value='', regex=True, inplace=True)
            logger.info('Adicionando o número DDI no início das colunas')
            for column in columns:
                 self.dataframe[column] = '55' + self.dataframe[column]
            
            logger.info(f'Success : Time = {round(time() - start_time,1)}s')
        except Exception as e:
            logger.error(
                f'Error : Time = {round(time() - start_time,1)}s : Exception = {e}')
            
    def _from_percentage_to_decimal(self, columns):
        start_time = time()
        try:
            for column in columns:
                logger.info(f'Convertendo coluna {column} de porcentagem para decimal (e.g., 80% para 0.8)')
                self.dataframe[column] = self.dataframe[column].str.replace('%', '').astype(float) / 100

            logger.info(f'Success : Time = {round(time() - start_time,1)}s')
        except Exception as e:
            logger.error(f'Error : Time = {round(time() - start_time,1)}s : Exception = {e}')

    def _cut_decimal_values(self, columns):
        start_time = time()
        try:
            logger.info(f'Removendo valores após o ponto/vírgula das colunas e adicionando o sufixo "h" (e.g., 80.5 para 80h)')
            for column in columns:
                self.dataframe[column].replace(to_replace=r',', value='.', regex=True, inplace=True)
                self.dataframe[column] = self.dataframe[column].str.split('.').str[0]
                self.dataframe[column] = self.dataframe[column].astype(str) + 'h'

            logger.info(f'Success : Time = {round(time() - start_time,1)}s')
        except Exception as e:
            logger.error(f'Error : Time = {round(time() - start_time,1)}s : Exception = {e}')

    def _fill_empty_columns(self):
        start_time = time()
        try:
            logger.info('Preenchendo colunas vazias')
            self.dataframe.fillna('', inplace=True)
            logger.info(f'Success : Time = {round(time() - start_time,1)}s')
        except Exception as e:
            logger.error(f'Error : Time = {round(time() - start_time,1)}s : Exception = {e}')
            

class IpedService(object):

    def __init__(self, url) -> None:
        self.url = url

    def get_csv_file(self) -> DataFrame:
        start_time = time()
        response = requests.get(self.url)
        if response.status_code != 200:
            raise Exception(
                f'Error : Status Code = {response.status_code} : Reason = {response.reason}')

        raw_csv = response.text
        csv = StringIO(raw_csv)
        dataframe = pd.read_csv(csv, sep=";")

        logger.info(f'Success : Time = {round(time() - start_time,1)}s')
        return dataframe


class SalesforceService(object):

    def __init__(self, dataframe) -> None:
       self.dataframe = dataframe
    
    def send_data(self):
        pass


class IpedSalesforceIntegrator(object):

    def __init__(self, config_filename='ipedSalesforceIntegrator.conf') -> None:
        # super(IpedSalesforceIntegrator, self).__init__(config_filename)
        # self.tryLock(self.pidFile) TODO: Decoment this line after integrating with the main code

        self.module_name = 'Integrador de dados IPED-Salesforce'
        logger.info(f'Iniciando o módulo {self.module_name}')

        self.config_filename = config_filename
        self._parse_module_dependent_config()

    def _parse_module_dependent_config(self):
        logger.info('Parseando o arquivo de configuração único do módulo')

        # TODO: Remove this line after integrating with the main code
        self.configParser = ConfigParser()
        # TODO: Remove this line after integrating with the main code
        self.configParser.read(self.config_filename)

        section = 'Iped'
        iped_config_required_fields = ['BASE_URL', 'USERNAME', 'USER_TOKEN']
        self._validate_required_args(section, iped_config_required_fields)

        required_placeholders = '<USERNAME>:<USER_TOKEN>'
        url = self.configParser[section]['BASE_URL']
        if required_placeholders not in url:
            # TODO: Change to ModuleInitException after integrating with the main code
            raise Exception(
                f'O campo BASE_URL deve conter o placeholder {required_placeholders}')

        self.iped_url = url.replace(
            required_placeholders, self.configParser[section]['USERNAME'] + ':' + self.configParser[section]['USER_TOKEN']).replace('\'', '')

    def _validate_required_args(self, section, required_fields):
        if (not self.configParser.has_section(section)):
            raise Exception(
                f'Arquivo de configuração não possui a seção [{section}]')  # TODO: Change to ModuleInitException after integrating with the main code

        for field in required_fields:
            if (not self.configParser.has_option(section, field)):
                raise Exception(
                    f'Arquivo de configuração não possui o campo {field} na seção [{section}]')  # TODO: Change to ModuleInitException after integrating with the main code

    def run(self):
        try:
            start_time = time()
            logger.info(
                f'Iniciando o processo de integração de dados IPED-Salesforce')

            logger.info(f'Obtendo o arquivo CSV do IPED')
            iped_service = IpedService(self.iped_url)
            df = iped_service.get_csv_file()

            logger.info(f'Processando o arquivo CSV')
            table_processor = TableProcessor(df)
            df = table_processor.process()

            logger.info(f'Enviando o arquivo CSV para o Salesforce/SFTP')
            salesforce = SalesforceService(df)
            salesforce.send_data()

            #df.to_excel('ipedSalesforceIntegrator.xlsx', index=False)
            #print(df.head())
            logger.info(f'Success : Processo executado com sucesso em {round(time() - start_time,1)}s')
        except Exception as e:
            logger.critical(
                f'Erro terminal durante a execução do módulo: {e} : {traceback.format_exc()}')


if __name__ == '__main__':
    logger.basicConfig(
        level=logger.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logger.StreamHandler()
        ]
    )

    integrator = IpedSalesforceIntegrator()
    integrator.run()
