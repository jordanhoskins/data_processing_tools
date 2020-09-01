"""
This script flattens hierarchical data into a list of flat dicts, where each value is non-iterable.
"""

import sys, json, pandas as pd


def get_recursive_data(nested_obj, keys) -> dict:
	"""
	This function plumbs the depths of hierarchical data until it reaches a non-hierarchical endpoint. When it
	encounters a non-dict value for a particular key, it records the address of that key using all higher-level keys
	joined with '..'. It will then back off one level, and continue recursion until all non-nested endpoints have been
	reached.
	Args:
		nested_obj (dict): A dict with values that are also dict, e.g. {'a': {'nested': 'dict'}}
		keys (list): List of previously encountered keys. These are joined with '..' to create the new keys in output.
	Returns:
		data (dict): A flat dict without nested values.
			{'a': {'nested': {'dict': 'is_very_cool'}}} -> {'a..nested..dict': 'is_very_cool'}
			{'a': {'nested': {'dict': ['with', 'multiple_values']}} ->
			{'a..nested..dict..0': 'with', 'a..nested..dict..1': 'multiple_values}
	"""
	k = keys
	data = {}
	for key in nested_obj:
		k.append(key)
		if type(nested_obj[key]) is dict:
			data.update(get_recursive_data(nested_obj[key], k))
		elif type(nested_obj[key]) is list:
			for index, element in enumerate(nested_obj[key]):
				k.append(str(index))
				if type(element) in {list, dict}:
					data.update(get_recursive_data(nested_obj[key][index], k))
				else:
					data[f"{'..'.join(k)}"] = element
				k.pop()
		else:
			data[f"{'..'.join(k)}"] = nested_obj[key]
		k.pop()

	return data


def explode(input_dict) -> list:
	"""
	This function explodes a nested dict into a list of flat dicts (all values are non-iterables). In annotation content
	types, the history field contains annotation objects with keys identical to the top-level data (i.e. all keys
	except history). Because of this, items from history are added as unique elements.
	Args:
		input_dict (dict): The dictionary to explode
	Returns:
		all_data (list): A list of dicts containing the non-iterable values from all keys in input_dict. In the case of
			deep hierarchical data, values are keyed by a string of '..'-joined keys from each level in the hierarchy.
			{'a': {'nested': {'dict': 'is_very_cool'}}} -> {'a..nested..dict': 'is_very_cool'}
	"""
	current_element_data = {}  # container for current element
	all_data = []  # each element in this list will be a line in final output

	for key in input_dict:
		if type(input_dict[key]) is list:
			for i in input_dict[key]:
				all_data.extend(explode(i))
		elif type(input_dict[key]) is dict:
			current_element_data.update(get_recursive_data(input_dict[key], keys=[key]))
		else:
			current_element_data[key] = input_dict[key]
	all_data.append(current_element_data)
	return all_data


if __name__ == '__main__':
	all_records = []
	with open(sys.argv[1]) as ifp:
		j_data = (json.loads(l) for l in ifp)
		for j_record in j_data:
			single_record = explode(j_data.get('value'))
			all_records.extend(single_record)
		df = pd.DataFrame(all_records)
		df.to_csv('test_csv.csv')
