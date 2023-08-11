from requests import Response

def validate_response(response: Response, mandatory_keys: [str]):
	if response.status_code != 200:
		raise Exception(
			f'Erro ao buscar dados no IPED: {response.status_code} - {response.text}')

	json = response.json()
	if 'STATE' not in json:
		raise Exception(f'JSON sem chave de indicação de estado STATE : {json}')

	if json['STATE'] != 1:
		raise Exception(f'Estado de retorno diferente de sucesso : {json}')

	for key in mandatory_keys:
		if key not in json:
			raise Exception(f'JSON sem chave obrigatória {key} : {json}')
		
def to_array_query_param(query_params, key, array: [str]) -> str:
	for index in range(0, len(array)):
		field = array[index]
		query_params[f"{key}[{index}]"] = field

	return query_params
