from ipedSalesforceIntegrator import SalesforceService, SalesforceConfig, User

def test_append_user_to_salesforce_send_buffer():
    salesforce = SalesforceService(None)

    user = User(1, 'Nome', 'Token')
    salesforce.append_user_to_sendbuffer(user)

    assert len(salesforce.sendbuffer) == 1
    assert salesforce.buffer_size > 0


def test_salesforce_config_parse():
    parser = {
        'CLIENT_ID': '123',
        'CLIENT_SECRET': '456',
        'BASE_URL': 'www.teste.com.br',
        'DATAEVENTS_ENDPOINT': '/dataevents/key:123/rowset'
    }

    salesforce_config = SalesforceConfig(parser)

    assert salesforce_config.client_id == '123'
    assert salesforce_config.client_secret == '456'
    assert salesforce_config.dataevents_url == 'www.teste.com.br/dataevents/key:123/rowset'


def test_buffer_ready_to_send():
	salesforce = SalesforceService(None)

	salesforce.buffer_size = 10
	assert salesforce.buffer_ready_to_send() == False

	salesforce.buffer_size = 100000000
	assert salesforce.buffer_ready_to_send() == True
