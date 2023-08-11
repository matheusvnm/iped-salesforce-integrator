from enum import Enum


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
        self.rate = ''             # Não temos essa informação do usuário
        self.category = ''
        self.hours = 0
        self.conclusion_rate = 0
        self.finished_hours = 0

        self.start_date = ''  # NOTE: Somente no Endpoint de cursos em concluídos
        self.conclusion_date = ''  # NOTE: Somente no Endpoint de cursos em concluídos
        self.last_access = ''  # NOTE: No endpoint de resumo do curso (Individual para Cada Curso)
        self.state = ''  # NOTE: Não existe nos endpoints de cursos

    def init_with_basic_info(self, json: dict) -> None:
        self.id = json['course_id']
        self.name = json['course_title']
        self.rate = json['course_rating']
        self.category = json['course_category_title']
        self.hours = json['course_hours']
        self.conclusion_rate = json['course_user']['user_course_completed']
        self._calculate_finished_hours()

    def _calculate_finished_hours(self) -> None:
        self.finished_hours = round(
            self.hours * (self.conclusion_rate / 100), 1)
        self.state = CourseState.CONCLUIDO if self.conclusion_rate == 100 else CourseState.CURSANDO

    def __str__(self) -> str:
        return f'Course(id={self.id}, name={self.name}, rate={self.rate}, hours={self.hours}, finished_hours={self.finished_hours}, conclusion_rate={self.conclusion_rate}, initial_date={self.start_date}, conclusion_date={self.conclusion_date}, last_access={self.last_access}, state={self.state})'


class User:

    def __init__(self, id: int, name: str, token: str, filial: bool = False) -> None:
        self.id = id
        self.name = name
        self.token = token
        self.filial = filial

        self.points = 0
        self.type = None
        self.cpf = None
        self.email = None
        self.trails = '' # TODO: Verificar se é necessário pegar esse campo.
        self.courses = []

    def __str__(self) -> str:
        return f'User(id={self.id}, name={self.name}, type={self.type}, cpf={self.cpf}, email={self.email}, points={self.points}, cellphone={self.cellphone}, trilhas={self.trilhas}, courses={self.courses})'