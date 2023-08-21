import pandas as pd

from ipedSalesforceIntegrator import TableProcessor


def test_fill_nan_with_empty_string():
	dataframe = pd.DataFrame({'A': [1, 2, pd.NaT], 'B': [pd.NaT, 3, 4]})
	processor = TableProcessor(dataframe)
	processor._fill_empty_columns()

	assert processor.dataframe['A'].isnull().sum() == 0
	assert processor.dataframe['B'].isnull().sum() == 0
	assert processor.dataframe['A'][2] == ''
	assert processor.dataframe['B'][0] == ''

def test_drop_columns():
	dataframe = pd.DataFrame({'A': [1, 2, pd.NaT], 'B': [pd.NaT, 3, 4]})
	processor = TableProcessor(dataframe)
	processor._drop_columns(columns=['A'])

	assert 'A' not in processor.dataframe.columns
	assert 'B' in processor.dataframe.columns

def test_standarlize_dates():
	dataframe = pd.DataFrame({'A': ['05/05/2023 00:00', '2020-01-02 00:00', '0000-00-00 00:00:00']})
	processor = TableProcessor(dataframe)
	processor._standarlize_dates(columns=['A'])

	assert processor.dataframe['A'][0] == '05/05/2023'
	assert processor.dataframe['A'][1] == '02/01/2020'
	assert not processor.dataframe['A'][2] == '0000-00-00 00:00:00'

def test_remove_phone_mask():
	dataframe = pd.DataFrame({'A': ['(11) 1234-5678', '11987654321', '11-98765-4321']})
	processor = TableProcessor(dataframe)
	processor._remove_phone_mask(columns=['A'])

	assert processor.dataframe['A'][0] == '551112345678'
	assert processor.dataframe['A'][1] == '5511987654321'
	assert processor.dataframe['A'][2] == '5511987654321'

def test_from_percentage_to_decimal():
	dataframe = pd.DataFrame({'A': ['100%', '50%', '25%']})
	processor = TableProcessor(dataframe)
	processor._from_percentage_to_decimal(columns=['A'])

	assert processor.dataframe['A'][0] == 1.0
	assert processor.dataframe['A'][1] == 0.5
	assert processor.dataframe['A'][2] == 0.25


def test_cut_decimal_values():
	dataframe = pd.DataFrame({'A': ['1.0', '50.0', '0.32', '0.004', '2.35']})
	processor = TableProcessor(dataframe)
	processor._cut_decimal_values(columns=['A'])

	assert processor.dataframe['A'][0] == '1h'
	assert processor.dataframe['A'][1] == '50h'
	assert processor.dataframe['A'][2] == '0h'
	assert processor.dataframe['A'][3] == '0h'
	assert processor.dataframe['A'][4] == '2h'

