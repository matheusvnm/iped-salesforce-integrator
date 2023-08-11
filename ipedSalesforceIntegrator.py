from time import time
from configparser import ConfigParser

from models import UserType
from services import IpedUserService, IpedTrailService, IpedCourseService, SalesforceService
from configs import IpedUserServiceConfig, IpedTrailServiceConfig, IpedCourseServiceConfig, SalesforceConfig, IpedAuthToken

# Importações a remover abaixo
import logging as logger


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
        iped_config_required_fields = ['TOKEN_FILIAL', 'TOKEN_MATRIZ', 'BASE_URL',
                                       'GET_TRAILS_ENDPOINT', 'GET_USERS_ENDPOINT', 'GET_USER_PROFILE_ENDPOINT',
                                       'GET_ALL_COURSES_ENDPOINT', 'GET_FINISHED_COURSES_ENDPOINT', 'GET_INPROGRESS_COURSES_ENDPOINT', 'GET_COURSE_SUMMARY_ENDPOINT'
                                       ]
        self._validate_required_args(section, iped_config_required_fields)

        auth_token = IpedAuthToken(self.configParser[section])

        self.user_config = IpedUserServiceConfig(
            self.configParser[section], auth_token)
        self.trail_config = IpedTrailServiceConfig(
            self.configParser[section], auth_token)
        self.course_config = IpedCourseServiceConfig(
            self.configParser[section], auth_token)

        section = 'Salesforce'
        salesforce_config_required_fields = [
            'CLIENT_ID', 'CLIENT_SECRET', 'BASE_URL', 'DATAEVENTS_ENDPOINT']
        self._validate_required_args(
            section, salesforce_config_required_fields)
        self.salesforce_config = SalesforceConfig(self.configParser[section])

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
            user_service = IpedUserService(self.user_config)
            trail_service = IpedTrailService(self.trail_config)
            course_service = IpedCourseService(self.course_config)
            salesforce_service = SalesforceService(self.salesforce_config)

            logger.info('Iniciando a busca de usuários no IPED')
            users = user_service.get_users_basic_info()
            user_len = len(users)

            logger.info('Iniciando a busca de perfis de usuários no IPED')
            for i in range(user_len - 1, 0, -1):
                start_user_time = time()
                user = users[i]
                logger.info(f'Processando {i} de {user_len - 1} usuários')

                #logger.info(f'Buscando informações completas do usuário : ID={user.id} - Nome={user.name}')
                user = user_service.get_user_full_info(user)
                if user.type != UserType.PLANO_ILIMITADO:
                    logger.info(f'[DEBUG] ID={user.id} - Type={user.type} - Nome={user.name} - Filial={user.filial}')

                '''
                logger.info(f'Buscando trilhas do usuário')
                user = trail_service.get_user_trails(user)

                logger.info(f'Buscando cursos do usuário')
                user = course_service.get_user_courses(user)

                # TODO: Verificar se a trilha de cursos é necessária
                logger.info(
                    f'Inserindo usuário na lista de envio para o Salesforce')
                salesforce_service.append_user_to_sendbuffer(user)

                if salesforce_service.buffer_ready_to_send():
                    logger.info(
                        f'Enviando requisição com dados dos usuários para o Salesforce')
                    salesforce_service.send_request()
                
                logger.info(f'Success : ID={user.id} - Cursos={len(user.courses)} - Trilhas={len(user.trails)} : Time={round(time() - start_user_time, 1)}s')

            # Se nós buscarmos todos o usuários e não enchermos o buffer, ao final da execução do for, o buffer será enviado mesmo sem estar cheio.
            salesforce_service.send_request()
            '''
            logger.info(f'Success: Time={round(time() - start_time, 1)}s')

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
