from ipedSalesforceIntegrator import IpedService, IpedConfig
from pytest_mock import mocker


def test_get_users_basic_info_from_iped(mocker):
    config = IpedConfig(dict())
    service = IpedService(config)

    matriz_users = [
        {
            'user_id': 1,
            'user_name': 'Nome 1',
            'user_token': 'Token 1'
        },
        {
            'user_id': 2,
            'user_name': 'Nome 2',
            'user_token': 'Token 2'
        }
    ]

    filial_users = [
        {
            'user_id': 3,
            'user_name': 'Nome 3',
            'user_token': 'Token 3'
        },
        {
            'user_id': 4,
            'user_name': 'Nome 4',
            'user_token': 'Token 4'
        }
    ]

    mocker.patch('ipedSalesforceIntegrator.IpedService._do_get_users_request',
                 return_value=[matriz_users, filial_users])
    users = service.search_user_basic_info()

    assert len(users) == 4
    for user in users:
        assert user.id in [1, 2, 3, 4]
        assert user.name in ['Nome 1', 'Nome 2', 'Nome 3', 'Nome 4']
        assert user.token in ['Token 1', 'Token 2', 'Token 3', 'Token 4']


def test_last_page():
    service = IpedService(None)
    json = {
        'TOTAL_PAGES': 1,
        'CURRENT_PAGE': 1
    }

    assert service._last_page(json) == True

    json = {
        'TOTAL_PAGES': 1,
        'CURRENT_PAGE': 2
    }

    assert service._last_page(json) == True

    json = {
        'TOTAL_PAGES': 2,
        'CURRENT_PAGE': 1
    }

    assert service._last_page(json) == False


'''
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
'''
