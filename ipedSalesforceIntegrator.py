from time import time
from enum import Enum
from typing import Dict
from datetime import datetime
from configparser import ConfigParser
from requests import Response, post


# Importações a remover abaixo
import logging as logger 

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
    CANCELADO = 'Cancelado'


class Course:

    def __init__(self, id: str, name: str, hours: int, finished_hours: float, conclusion_rate: str, 
                initial_date: datetime, conclusion_date: datetime, last_access: datetime, 
                state: CourseState, points: int, rate: int, brief: str) -> None:
        self.id = id
        self.name = name
        self.hours = hours
        self.finished_hours = finished_hours
        self.conclusion_rate = conclusion_rate
        self.initial_date = initial_date
        self.conclusion_date = conclusion_date
        self.last_access = last_access
        self.state = state
        self.points = points
        self.rate = rate
        self.brief = brief


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

class IpedService:

	def __init__(self, config: dict) -> None:
		self._get_users_url = config.get('GET_USERS_URL')
		self._get_courses_url = config.get('GET_COURSES_URL')
		self._get_user_profile_url = config.get('GET_USER_PROFILE_URL')
		self._token_matriz = config.get('TOKEN_MATRIZ')
		self._token_filial = config.get('TOKEN_FILIAL')
        
	def _search_all_users(self) -> Dict[int, str]:
		logger.info('Buscando usuários na matriz')
		start_time = time()
		user_json = self._do_get_users_request(self._token_matriz)

		logger.info('Processando usuários da matriz')
		users = dict()
		for user in user_json:
			id = user['user_id']
			users[id] = User(id, user['user_name'], user['user_token'])

		logger.info('Buscando usuários da filial')
		user_json = self._do_get_users_request(self._token_filial)

		logger.info('Processando usuários da filial')
		for user in user_json:
			id = user['user_id']
			if id not in users:
				users[id] = User(id, user['user_name'], user['user_token'], True)

		logger.info(f'Foram encontrados {len(users)} usuários no total : Time={round(time() - start_time, 1)}s')
		return users
	
	def _do_get_users_request(self, token: str) -> Response:
		form_data = {'api_version': '2', 'token': token}
		response = post(self._get_users_url, data=form_data)
		self._validate_response(response, ['USERS'])
		users = response.json()['USERS']
		return users
             
	def _validate_response(self, response: Response, mandatory_keys: [str]):
		if response.status_code != 200:
			raise Exception(f'Erro ao buscar usuários no IPED: {response.status_code} - {response.text}')

		if 'STATE' not in response.json().keys():
			raise Exception(f'Erro ao buscar usuários no IPED: {response.json()}')
		
		if response.json()['STATE'] != 1:
			raise Exception(f'Erro ao buscar usuários no IPED: {response.json()}')

		for key in mandatory_keys:
			if key not in response.json().keys():
				raise Exception(f'Erro ao buscar usuários no IPED: {response.json()}')


	def _search_user_profile(self, id: int, api_token: str, user_token: str) -> User:
		form_data = {'api_version': '2', 'token': api_token, 'user_id': id, 'user_token': user_token}
		response = post(self._get_user_profile_url, data=form_data)
		self._validate_response(response, ['PROFILE'])
		user_json = response.json()['PROFILE']

		return (user_json['user_cpf'], user_json['user_email'], UserType(user_json['user_type']))
        
	def _search_user_courses(self, id: int, api_token: str) -> [Course]:
		form_data = {'api_version': '2', 'token': api_token, 'user_id': id}
		response = post(self._get_courses_url, data=form_data)
		self._validate_response(response, ['COURSES'])
		courses_json = response.json()['COURSES']

		courses = list()
		for course_json in courses_json:
			course = Course(course_json)
			courses.append(course)
		
		return courses
        
	def search_users_infos(self) -> dict():
		logger.info('Buscando todos os usuários do IPED')
		users = self._search_all_users()

		i = 1
		total_users = len(users)

		logger.info('Buscando os perfis de cada usuário')
		for id, user in users.items():
			logger.info(f'Buscando o perfil do usuário {i} de {total_users} : UserID={id}')

			start_time = time()
			api_token = self._token_matriz if not user.filial else self._token_filial
			(user.cpf, user.email, user.type) = self._search_user_profile(id, api_token, user.token)
			#user.courses = self._search_user_courses(id, api_token, user.token)
			logger.info(f'Success : {user} : Time={round(time() - start_time, 1)}s')

			if i == 5:
				break
			i += 1
	
		return users


class SalesforceService:

	def __init__(self, config: dict) -> None:
		self._client_id = config.get('CLIENT_ID')
		self._client_secret = config.get('CLIENT_SECRET')
		self._dataevents_url = config.get('DATAEVENTS_URL')


class IpedSalesforceIntegrator(object): 

	def __init__(self, config_filename='ipedSalesforceIntegrator.conf') -> None:
		#super(IpedSalesforceIntegrator, self).__init__(config_filename)
        #self.tryLock(self.pidFile) TODO: Decoment this line after integrating with the main code

		self.module_name = 'Integrador de dados do IPED com o Salesforce'
		logger.info(f'Iniciando o módulo {self.module_name}')

		self.config_filename = config_filename
		self._parse_module_dependent_config()
	
	def _parse_module_dependent_config(self):
		logger.info('Parseando o arquivo de configuração único do módulo')

		self.configParser = ConfigParser() # TODO: Remove this line after integrating with the main code
		self.configParser.read(self.config_filename) # TODO: Remove this line after integrating with the main code

		section = 'Iped'
		iped_config_required_fields = ['TOKEN_FILIAL', 'TOKEN_MATRIZ', 'BASE_URL', 'GET_COURSES_ENDPOINT', 'GET_USERS_ENDPOINT', 'GET_USER_PROFILE_ENDPOINT']
		self._validate_required_args(section, iped_config_required_fields)

		self.iped_config = dict()
		self.iped_config['GET_COURSES_URL'] = f"{self.configParser.get(section, 'BASE_URL')}{self.configParser.get(section, 'GET_COURSES_ENDPOINT')}"
		self.iped_config['GET_USERS_URL'] = f"{self.configParser.get(section, 'BASE_URL')}{self.configParser.get(section, 'GET_USERS_ENDPOINT')}"
		self.iped_config['GET_USER_PROFILE_URL'] = f"{self.configParser.get(section, 'BASE_URL')}{self.configParser.get(section, 'GET_USER_PROFILE_ENDPOINT')}"
		self.iped_config['TOKEN_MATRIZ'] = self.configParser.get(section, 'TOKEN_MATRIZ')
		self.iped_config['TOKEN_FILIAL'] = self.configParser.get(section, 'TOKEN_FILIAL')

		section = 'Salesforce'
		salesforce_config_required_fields = ['CLIENT_ID', 'CLIENT_SECRET', 'BASE_URL', 'DATAEVENTS_ENDPOINT']
		self._validate_required_args(section, salesforce_config_required_fields)

		self.salesforce_config = dict()
		self.salesforce_config['CLIENT_ID'] = self.configParser.get(section, 'CLIENT_ID')
		self.salesforce_config['CLIENT_SECRET'] = self.configParser.get(section, 'CLIENT_SECRET')
		self.salesforce_config['DATAEVENTS_URL'] = f"{self.configParser.get(section, 'BASE_URL')}{self.configParser.get(section, 'DATAEVENTS_ENDPOINT')}"


	def _validate_required_args(self, section, required_fields):
		if (not self.configParser.has_section(section)):
			raise Exception(
				f'Arquivo de configuração não possui a seção [{section}]') # TODO: Change to ModuleInitException after integrating with the main code

		for field in required_fields:
			if (not self.configParser.has_option(section, field)):
				raise Exception(
					f'Arquivo de configuração não possui o campo {field} na seção [{section}]') # TODO: Change to ModuleInitException after integrating with the main code

	def run(self):
		try:
			start_time = time()
			iped = IpedService(self.iped_config)

			logger.info('Executando a busca no serviço do IPED')
			users = iped.search_users_infos()
			qtd_users = len(users)
			logger.info(f'Foram encontrados {qtd_users} usuários.')

			#logger.info('Executando a inserção no serviço do Salesforce')
			#salesforce = SalesforceService(self.salesforce_config)
			#(inserts, errors) = salesforce.insert_users(users)

			#logger.info(f'Foram inseridos {inserts} usuários com sucesso e {errors} falharam.')
			logger.info(f'Success: Time={round(time() - start_time, 1)}s')
		except Exception as e:
			logger.critical(
				f'Erro terminal durante a execução do módulo: {str(e)}')


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