import unicodedata

def normalize_city_name(city):
    city_normalized = unicodedata.normalize('NFKD', city).encode('ascii', 'ignore').decode('ascii')
    city_normalized = city_normalized.lower().replace(' ', '_')
    return city_normalized
