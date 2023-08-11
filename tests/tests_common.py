import pytest

from common import validate_response

def test_response_validation_with_invalid_status_code(mocker):
    response = mocker.Mock()
    response.status_code = 500
    response.text = 'Erro'

    with pytest.raises(Exception) as e:
        validate_response(response, ['STATE'])
        assert '500' in str(e)

def test_response_validation_with_invalid_state(mocker):
    response = mocker.Mock()
    response.status_code = 200
    response.json.return_value = {
        'STATE': 0
    }

    with pytest.raises(Exception) as e:
        validate_response(response, ['STATE'])
        assert 'STATE' in str(e)

def test_response_validation_with_no_state(mocker):
    response = mocker.Mock()
    response.status_code = 200
    response.json.return_value = {}

    with pytest.raises(Exception) as e:
        validate_response(response, ['STATE'])
        assert 'STATE' in str(e)

def test_response_validation_with_invalid_mandatory_key(mocker):
    response = mocker.Mock()
    response.status_code = 200
    response.json.return_value = {
        'STATE': 1
    }

    with pytest.raises(Exception) as e:
        validate_response(response, ['STATE', 'MANDATORY_KEY'])
        assert 'MANDATORY_KEY' in str(e)

def test_response_validation_with_valid_response(mocker):
    response = mocker.Mock()
    response.status_code = 200
    response.json.return_value = {
        'STATE': 1,
        'MANDATORY_KEY': 'value'
    }

    validate_response(response, ['STATE', 'MANDATORY_KEY'])

