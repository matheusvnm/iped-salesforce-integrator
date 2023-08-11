import sys
import traceback
import logging as logger


from time import time
from requests import Response, post
from models import User, UserType, Course
from configs import SalesforceConfig, IpedUserServiceConfig, IpedTrailServiceConfig, IpedCourseServiceConfig
from common import validate_response, to_array_query_param

class IpedUserService:
    
    

    def __init__(self, config: IpedUserServiceConfig) -> None:
        self.users = {}
        self.user_retry = {}
        self.config = config
    
    def get_users_basic_info(self) -> [User]:
        start_time = time()

        logger.info('Buscando usuários na empresa matriz')
        users_matriz = self._do_get_users_request(self.config.get_users_url, self.config.token())
        self._process_basic_users_info(users_matriz)

        logger.info('Buscando usuários na empresa filial')
        users_filial = self._do_get_users_request(self.config.get_users_url, self.config.token(True))
        self._process_basic_users_info(users_filial, True)

        logger.info(
            f'Success : Users={len(self.users)} - Time={round(time() - start_time, 1)}s')
        return list(self.users.values())

    def _do_get_users_request(self, url: str, token: str):
        form_data = {'api_version': '2', 'token': token}
        response = post(url, data=form_data)
        validate_response(response, ['USERS'])
        users = response.json()['USERS']
        return users
    
    def _process_basic_users_info(self, users_json: dict(), filial: bool = False) -> None:
        try:
            for user in users_json:
                id = user['user_id']
                if id not in self.users:
                    self.users[id] = User(id, user['user_name'], user['user_token'], filial)
        except Exception as e:
            logger.error(f'Erro ao processar usuários : Filial={filial} - Exception= {e} : {traceback.format_exc()}')


    def get_user_full_info(self, user: User) -> User:
        api_token = self.config.token(user.filial)
        form_data = {'api_version': '2', 'token': api_token,
                     'user_id': user.id, 'user_token': user.token}
        try:
            response = post(self.config.get_user_profile_url, data=form_data)
            validate_response(response, ['PROFILE'])
            user_json = response.json()['PROFILE']

            user.cpf = user_json['user_cpf']
            user.email = user_json['user_email']
            user.points = user_json['user_ranking']['user_points']['total']
            user.type = UserType(user_json['user_type'])

            return user
        except Exception as e:
            logger.error(f'Erro ao buscar informações do usuário : ID={user.id} - Exception= {e} : {traceback.format_exc()}')
            if user.id not in self.user_retry:
                self.user_retry[user.id] = user
            return user

class IpedTrailService:

    def __init__(self, config: IpedTrailServiceConfig) -> None:
        self.config = config

    def get_user_trails(self, user: User):
        api_token = self.config.token(user.filial)
        form_data = {'api_version': '2', 'token': api_token,
                     'user_id': user.id, 'user_token': user.token}
        response = post(self.config.get_trails_url, data=form_data)
        validate_response(response, ['TRAILS'])
        trails_json = response.json()['TRAILS']

        user.trails = ''
        for trail_json in trails_json:
            user.trails += trail_json['trail_title']

        return user

class IpedCourseService:

    def __init__(self, config: IpedCourseServiceConfig) -> None:
        self.config = config
    
    def get_user_courses(self, user: User):
        if user.user_type == UserType.PLANO_ILIMITADO:
            #user.courses = self._get_users_courses(user)
            user.courses = []
        else:
            logger.info(f'[DEBUG] ID={user.id} - Type={user.user_type}')
            user.courses = []
            #user.courses = self._search_common_user_courses(user)

        return user
    
    def _get_users_courses(self, user):
        api_token = self.config.token(user.filial)
        form_data = {'api_version': '2', 'token': api_token,
                     'user_id': user.id, 'user_token': user.token}
        
        logger.info('Buscando IDs de cursos em andamento e finalizados')
        courses_ids = self._get_course_ids(self.config.get_inprogress_courses_url, form_data)
        courses_ids += self._get_course_ids(self.config.get_finished_courses_url, form_data)

        if len(courses_ids) == 0:
            return []

        form_data = to_array_query_param(form_data, 'course_id', courses_ids)

        logger.info('Buscando informações do cursos')
        page = 1
        last_page = False
        while not last_page:
            form_data['page'] = page
            response = post(self.config.get_all_courses_url, data=form_data)
            validate_response(response, ['COURSES'])

            courses = []
            json = response.json()
            courses_json = json['COURSES']

            for course_json in courses_json:
                course = Course()
                course.init_with_basic_info(course_json)
                courses.append(course)

            last_page = json['CURRENT_PAGE'] >= json['TOTAL_PAGES']
            page += 1

        form_data2 = {'api_version': '2', 'token': api_token,
                     'user_id': user.id, 'user_token': user.token}
        
        logger.info('Buscando informações restantes dos cursos')
        courses = self._get_remaining_courses_info(courses, form_data2)
        return courses
            
    def _get_course_ids(self, url, form_data):
        response = post(url, data=form_data)
        validate_response(response, ['COURSES'])
        courses_json = response.json()['COURSES']

        courses_ids = []
        for course_json in courses_json:
            courses_ids.append(course_json['course_id'])

        return courses_ids

    def _get_remaining_courses_info(self, courses, form_data):
        for course in courses:
            
            form_data['course_id'] = course.id
            response = post(self.config.get_course_summary_url, data=form_data)
            validate_response(response, ['SUMMARY'])
            course_summary_json = response.json()['SUMMARY']
            course_user = course_summary_json['course_user']

            course.start_date = course_user['user_course_date_start']
            course.last_access = course_user['user_course_date_lastaccess']
            course.conclusion_date = course_user['user_course_date_conclusion']

            logger.debug(f'{course}')

        return courses


class SalesforceService:

    # 5MB é o limite de payload para o Salesforce, porém 2MB é um limite seguro
    PAYLOAD_LIMIT_IN_BYTES = 2097152

    def __init__(self, config : SalesforceConfig) -> None:
        self.config = config
        self.sendbuffer = list()
        self.buffer_size = 0

    def append_user_to_sendbuffer(self, user: User) -> None:
        self.sendbuffer.append(user)
        courses_size = 0
        for course in user.courses:
            courses_size += sys.getsizeof(course)
        self.buffer_size += sys.getsizeof(user) + courses_size

    def buffer_ready_to_send(self) -> bool:
        logger.info(f'Tamanho da lista de envio {self.buffer_size} : Tamanho Mínimo {self.PAYLOAD_LIMIT_IN_BYTES}')
        return self.buffer_size >= self.PAYLOAD_LIMIT_IN_BYTES

    def send_request(self) -> None:
        start_time = time()
        if len(self.buffer_size) == 0:
            logger.info('Lista de envio vazia')
            return

        #json = self.build_payload()
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