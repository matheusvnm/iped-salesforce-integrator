class IpedAuthToken:
    
	def __init__(self, config) -> None:
		self.matriz_token = config.get('TOKEN_MATRIZ')
		self.filial_token = config.get('TOKEN_FILIAL')

	def get_token(self, filial: bool):
		return self.matriz_token if not filial else self.filial_token
	

class IpedUserServiceConfig:
	
	def __init__(self, config_urls: dict, auth_token: IpedAuthToken) -> None:
		self.get_users_url = f"{config_urls.get('BASE_URL') + config_urls.get('GET_USERS_ENDPOINT')}"
		self.get_user_profile_url = f"{config_urls.get('BASE_URL') + config_urls.get('GET_USER_PROFILE_ENDPOINT')}"
		self.auth_token = auth_token

	def token(self, filial: bool = False):
		return self.auth_token.get_token(filial)


class IpedTrailServiceConfig: 
	
	def __init__(self, config_urls: dict, auth_token: IpedAuthToken) -> None:
		self.get_trails_url = f"{config_urls.get('BASE_URL') + config_urls.get('GET_TRAILS_ENDPOINT')}"
		self.auth_token = auth_token
	
	def token(self, filial: bool = False):
		return self.auth_token.get_token(filial)
	

class IpedCourseServiceConfig:

	def __init__(self, config_urls: dict, auth_token: IpedAuthToken) -> None:
		self.get_all_courses_url = f"{config_urls.get('BASE_URL') + config_urls.get('GET_ALL_COURSES_ENDPOINT')}"
		self.get_inprogress_courses_url = f"{config_urls.get('BASE_URL') + config_urls.get('GET_INPROGRESS_COURSES_ENDPOINT')}"
		self.get_finished_courses_url = f"{config_urls.get('BASE_URL') + config_urls.get('GET_FINISHED_COURSES_ENDPOINT')}"
		self.get_course_summary_url = f"{config_urls.get('BASE_URL') + config_urls.get('GET_COURSE_SUMMARY_ENDPOINT')}"
		self.auth_token = auth_token
		
	def token(self, filial: bool = False):
		return self.auth_token.get_token(filial)


class SalesforceConfig:

    def __init__(self, parser):
        self.client_id = parser.get('CLIENT_ID')
        self.client_secret = parser.get('CLIENT_SECRET')
        self.dataevents_url = f"{parser.get('BASE_URL')}{parser.get('DATAEVENTS_ENDPOINT')}"
