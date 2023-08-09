from time import time
from enum import Enum
from typing import Dict
from datetime import datetime
from configparser import ConfigParser
from requests import Response, post


# Importações a remover abaixo
import logging as logger
import sys


class UserType(Enum):
    CURSO_GRATIS = 1
    CURSO_PLUS = 2
    CURSO_PREMIUM = 3
    PLANO_ILIMITADO = 4

    def __str__(self) -> str:
        return self.name


class CourseState(str, Enum):
    CONCLUIDO = 'Concluído'
    CURSANDO = 'Cursando'
    CANCELADO = 'Cancelado'  # Não existe nos endpoints de cursos


class Course:

    def __init__(self) -> None:
        self.id = ''
        self.name = ''
        self.rate = ''
        self.hours = 0
        self.points = 0
        self.finished_hours = 0
        self.conclusion_rate = 0
        self.initial_date = ''  # Somente no Endpoint de cursos em concluídos
        self.conclusion_date = ''  # Somente no Endpoint de cursos em concluídos
        self.last_access = ''  # Não existe nos endpoints de cursos
        self.state = ''  # Não existe nos endpoints de cursos

    def calculate_finished_hours(self) -> None:
        self.finished_hours = round(
            self.hours * (self.conclusion_rate / 100), 1)
        self.state = CourseState.CONCLUIDO if self.conclusion_rate == 100 else CourseState.CURSANDO

    def __str__(self) -> str:
        return f'Course(id={self.id}, name={self.name}, rate={self.rate}, hours={self.hours}, points={self.points}, finished_hours={self.finished_hours}, conclusion_rate={self.conclusion_rate}, initial_date={self.initial_date}, conclusion_date={self.conclusion_date}, last_access={self.last_access}, state={self.state})'


class User:

    def __init__(self, id: int, name: str, token: str, filial: bool = False) -> None:
        self.id = id
        self.name = name
        self.token = token
        self.filial = filial

        self.type = None
        self.cpf = None
        self.email = None
        self.cellphone = None
        self.trilhas = None
        self.courses = None

    def __str__(self) -> str:
        return f'User(id={self.id}, name={self.name}, type={self.type}, cpf={self.cpf}, email={self.email}, cellphone={self.cellphone}, trilhas={self.trilhas}, courses={self.courses})'


class IpedConfig:

    def __init__(self, parser):
        self.users_url = f"{parser.get('BASE_URL')}{parser.get('GET_USERS_ENDPOINT')}"
        self.user_profile_url = f"{parser.get('BASE_URL')}{parser.get('GET_USER_PROFILE_ENDPOINT')}"
        self.all_courses_url = f"{parser.get('BASE_URL')}{parser.get('GET_ALL_COURSES_ENDPOINT')}"
        self.inprogress_courses_url = f"{parser.get('BASE_URL')}{parser.get('GET_INPROGRESS_COURSES_ENDPOINT')}"
        self.finished_courses_url = f"{parser.get('BASE_URL')}{parser.get('GET_FINISHED_COURSES_ENDPOINT')}"

        self.token_matriz = parser.get('TOKEN_MATRIZ')
        self.token_filial = parser.get('TOKEN_FILIAL')


class IpedService:

    def __init__(self, config: IpedConfig) -> None:
        self.config = config

    def search_user_basic_info(self) -> [User]:
        logger.info('Buscando usuários na empresa matriz')
        start_time = time()
        user_json = self._do_get_users_request(
            self.config.users_url, self.config.token_matriz)

        users = dict()
        for user in user_json:
            id = user['user_id']
            users[id] = User(id, user['user_name'], user['user_token'])

        logger.info('Buscando usuários na empresa filial')
        user_json = self._do_get_users_request(
            self.config.users_url, self.config.token_filial)

        for user in user_json:
            id = user['user_id']
            if id not in users:
                users[id] = User(id, user['user_name'],
                                 user['user_token'], True)

        logger.info(
            f'Success : Users={len(users)} - Time={round(time() - start_time, 1)}s')
        return list(users.values())

    def _do_get_users_request(self, url: str, token: str) -> Response:
        form_data = {'api_version': '2', 'token': token}
        response = post(url, data=form_data)
        self._validate_response(response, ['USERS'])
        users = response.json()['USERS']
        return users

    def _validate_response(self, response: Response, mandatory_keys: [str]):
        if response.status_code != 200:
            raise Exception(
                f'Erro ao buscar dados no IPED: {response.status_code} - {response.text}')

        json = response.json()
        if 'STATE' not in json:
            raise Exception(f'Erro ao buscar dados no IPED: {json}')

        if json['STATE'] != 1:
            raise Exception(f'Erro ao buscar dados no IPED: {json}')

        for key in mandatory_keys:
            if key not in json:
                raise Exception(f'Erro ao buscar dados no IPED: {json}')

    def search_user_full_info(self, token: str, id: int, user_token: str) -> User:
        form_data = {'api_version': '2', 'token': token,
                     'user_id': id, 'user_token': user_token}
        response = post(self.config.user_profile_url, data=form_data)
        self._validate_response(response, ['PROFILE'])
        user_json = response.json()['PROFILE']

        return (user_json['user_cpf'], user_json['user_email'], UserType(user_json['user_type']))

    def _search_unlimited_user_courses(self, id: int, api_token: str, user_token: str) -> list():
        courses = self._search_inprogress_courses(id, api_token, user_token)
        finished_courses = self._search_finished_courses(
            id, api_token, user_token)
        courses.extend(finished_courses)

    def _search_inprogress_courses(self, id: int, api_token: str, user_token: str) -> list():
        logger.info('Buscando cursos em andamento')

        form_data = {'api_version': '2', 'user_id': id,
                     'token': api_token, 'user_token': user_token}
        response = post(self.config.inprogress_courses_url, data=form_data)
        self._validate_response(response, ['COURSES'])
        courses_json = response.json()['COURSES']

        courses = list()
        for json in courses_json:
            course = Course()
            course.id = json['course_id']
            course.name = json['course_title']
            course.rate = json['course_rating']
            course.hours = json['course_hours']
            course.points = json['course_user']['user_course_grade']
            course.conclusion_rate = json['course_user']['user_course_completed']
            course.calculate_finished_hours()

            courses.append(course)

        logger.info(f'Courses={len(courses)}')
        return courses

    def _search_finished_courses(self, id: int, api_token: str, user_token: str) -> list():
        logger.info('Buscando cursos concluídos')

        form_data = {'api_version': '2', 'user_id': id,
                     'token': api_token, 'user_token': user_token}
        response = post(self.config.finished_courses_url, data=form_data)
        self._validate_response(response, ['COURSES'])
        courses_json = response.json()['COURSES']

        courses = dict()
        for json in courses_json:
            course = Course()
            course.id = json['course_id']
            course.name = json['course_title']
            course.initial_date = json['course_date_start']
            course.conclusion_date = json['course_date_conclusion']

            courses[course.id] = course

        if len(courses) == 0:
            logger.info(f'Courses=0')
            return courses.values()

        page = 0
        last_page = False
        form_data['course_id[]'] = courses.keys()
        while not last_page:
            page += 1
            form_data['page'] = page
            response = post(self.config.all_courses_url, data=form_data)
            self._validate_response(
                response, ['COURSES', 'CURRENT_PAGE', 'TOTAL_PAGES'])
            json = response.json()
            courses_json = json['COURSES']

            for course_doc in courses_json:
                if course_doc['course_id'] in courses:
                    course = courses[course_doc['course_id']]
                    course.rate = course_doc['course_rating']
                    course.hours = course_doc['course_hours']
                    course.points = course_doc['course_user']['user_course_grade']
                    course.conclusion_rate = course_doc['course_user']['user_course_completed']
                    course.calculate_finished_hours()

            last_page = self._last_page(json)

        logger.info(f'Courses={len(courses.values())}')
        return courses.values()

    def _last_page(self, json) -> bool:
        return json['CURRENT_PAGE'] >= json['TOTAL_PAGES']

    def _search_common_user_courses(self, id: int, api_token: str, user_token: str) -> list():
        logger.info('Buscando cursos para usuários não ilimitados')

        form_data = {'api_version': '2', 'user_id': id, 'token': api_token, 'user_token': user_token, 'always_show': 1, 'results': 500}

        page = 0
        last_page = False
        courses = list()
        while not last_page:
            page += 1
            form_data['page'] = page
            response = post(self.config.all_courses_url, data=form_data)
            self._validate_response(response, ['COURSES', 'CURRENT_PAGE', 'TOTAL_PAGES'])

            json = response.json()
            courses_json = json['COURSES']
            for course_doc in courses_json:
                if course_doc['course_user']['user_course_completed'] == 0:
                    continue

                course = Course()
                course.id = course_doc['course_id']
                course.name = course_doc['course_title']
                course.rate = course_doc['course_rating']
                course.hours = course_doc['course_hours']
                course.points = course_doc['course_user']['user_course_grade']
                course.conclusion_rate = course_doc['course_user']['user_course_completed']
                course.calculate_finished_hours()

                courses.append(course)                

            last_page = self._last_page(json)
        
        logger.info(f'Courses={len(courses)}')

    def search_user_courses(self, token: str, id: int, user_token: str, user_type: UserType) -> [Course]:
        if user_type == UserType.PLANO_ILIMITADO:
            return self._search_unlimited_user_courses(id, token, user_token)
        else:
            logger.info(f'[DEBUG] ID={id} - Type={user_type}')
            return self._search_common_user_courses(id, token, user_token)

    def define_token(self, user: User) -> str:
        return self.config.token_matriz if not user.filial else self.config.token_filial


class SalesforceConfig:

    def __init__(self, parser):
        self.client_id = parser.get('CLIENT_ID')
        self.client_secret = parser.get('CLIENT_SECRET')
        self.dataevents_url = f"{parser.get('BASE_URL')}{parser.get('DATAEVENTS_ENDPOINT')}"


class SalesforceService:

    # 5MB é o limite de payload para o Salesforce, porém 2MB é um limite seguro
    PAYLOAD_LIMIT_IN_BYTES = 2097152

    def __init__(self, config) -> None:
        self.config = config
        self.sendbuffer = list()
        self.buffer_size = 0

    def append_user_to_sendbuffer(self, user: User) -> None:
        self.sendbuffer.append(user)
        self.buffer_size += sys.getsizeof(user)

    def buffer_ready_to_send(self) -> bool:
        shoud_send = self.buffer_size >= self.PAYLOAD_LIMIT_IN_BYTES
        logger.info(
            f'Tamanho da lista de envio {self.buffer_size} : Tamanho Mínimo {self.PAYLOAD_LIMIT_IN_BYTES}')
        return shoud_send

    def send_request(self) -> None:
        start_time = time()
        if len(self.buffer_size) == 0:
            logger.info('Lista de envio vazia')
            return

        #json = self.mount_payload()
        #response = post(self.config.dataevents_url, json=json,
        #                headers=self._get_headers())
        # self._validate_response(response)
        self.sendbuffer.clear()
        self.buffer_size = 0
        logger.info(f'Success : Time={round(time() - start_time, 1)}s')

        # TODO: Implementar

    def mount_payload(self) -> dict():
        # TODO:
        pass


class Integrator(object):

    def __init__(self, iped_service: IpedService, salesforce_service: SalesforceService) -> None:
        self.iped_service = iped_service
        self.salesforce_service = salesforce_service

    def run(self):
        logger.info('Iniciando a busca de usuários no IPED')
        iped_users = self.iped_service.search_user_basic_info()
        user_len = len(iped_users)

        logger.info('Iniciando a busca de perfis de usuários no IPED')
        for i in range(0, user_len, 1):
            user = iped_users[i]
            logger.info(
                f'Buscando informações extras para {i} de {user_len - 1} usuários : ID={user.id} - Nome={user.name}')

            token = self.iped_service.define_token(user)
            (user.cpf, user.email, user.type) = self.iped_service.search_user_full_info(
                token, user.id, user.token)

            logger.info(f'Buscando cursos do usuário')
            user.courses = self.iped_service.search_user_courses(
                token, user.id, user.token, user.type)

            logger.info(
                f'Inserindo usuário na lista de envio para o Salesforce')
            self.salesforce_service.append_user_to_sendbuffer(user)
            if self.salesforce_service.buffer_ready_to_send():
                logger.info(
                    f'Enviando requisição com dados dos usuários para o Salesforce')
                self.salesforce_service.send_request()

        # Se nós buscarmos todos o usuários e não enchermos o buffer, ao final da execução do for, o buffer será enviado.
        self.salesforce_service.send_request()


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
        iped_config_required_fields = ['TOKEN_FILIAL', 'TOKEN_MATRIZ', 'BASE_URL', 'GET_ALL_COURSES_ENDPOINT',
                                       'GET_FINISHED_COURSES_ENDPOINT', 'GET_INPROGRESS_COURSES_ENDPOINT', 'GET_USERS_ENDPOINT', 'GET_USER_PROFILE_ENDPOINT']
        self._validate_required_args(section, iped_config_required_fields)
        self.iped_config = IpedConfig(self.configParser[section])

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
            iped_service = IpedService(self.iped_config)
            salesforce_service = SalesforceService(self.salesforce_config)
            integrator = Integrator(iped_service, salesforce_service)
            integrator.run()
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
