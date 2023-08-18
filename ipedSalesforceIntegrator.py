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
        self._drop_unnecessary_columns()
        self._standarlize_date_columns()
        return self.dataframe

    def _drop_unnecessary_columns(self):
        start_time = time()

        try:
            logger.info('Removendo colunas desnecessárias')
            columns = ['Depoimento']
            self.dataframe.drop(columns, inplace=True, axis=1)
            logger.info(
                f'Success : Time = {time() - start_time}s : Removed = {columns}')
        except Exception as e:
            logger.error(
                f'Error : Time = {time() - start_time}s : Exception = {e}')

    def _standarlize_date_columns(self):
        start_time = time()

        try:
            logger.info('Padronizando colunas de data')
            invalid_date = ['0000-00-00 00:00:00']
            self.dataframe.replace(to_replace=invalid_date, value='', inplace=True)
            #replace the dateformat from dd/mm/yyyy hh:mm to dd/mm/yyyy
            self.dataframe['Data Início'] = pd.to_datetime(self.dataframe['Data Início'], format='%d/%m/%Y %H:%M:%S').dt.strftime('%d/%m/%Y')
            
            
            #for column in []
            #self.dataframe['Data de Nascimento'] = self.dataframe['Data de Nascimento'].str[:10]
            #self.dataframe['Data de Início'] = self.dataframe['Data de Início'].str[:10]

            logger.info(f'Success : Time = {time() - start_time}s')
        except Exception as e:
            logger.error(
                f'Error : Time = {time() - start_time}s : Exception = {e}')


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

        logger.info(f'Success : Time = {time() - start_time}s')
        return dataframe


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
            # salesforce = SalesforceService(df)
            # salesforce.dispatch_to_sftp()
            logger.info(
                f'Success : Processo executado com sucesso em {time() - start_time}s')
        except Exception as e:
            e.with_traceback()
            logger.critical(
                f'Erro terminal durante a execução do módulo: {e}')


if __name__ == '__main__':
    logger.basicConfig(
        level=logger.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logger.FileHandler("ipedSalesforceIntegrator.log"),
            logger.StreamHandler()
        ]
    )

    integrator = IpedSalesforceIntegrator()
    integrator.run()
