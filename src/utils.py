import zipcode

def get_plain_text(text, list_of_indices):
	start = 0
	plain_text = ""
	list_of_indices.sort(key=lambda x: x[0])
	
	for indices in list_of_indices:
		plain_text += text[start:indices[0]]
		start = indices[1] + 1
	plain_text += text[start:]
	return plain_text

def coords2zipcode(latlon, radius=1.5):
    try:
		return zipcode.isinradius(latlon, radius)[0].zip
	except:
		return None
