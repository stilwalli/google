def get_service_center_by_city(city:str) -> str:
  """
  This function returns service center addresses for a given city.
  Args:
    city (str): name of the city.
  Returns:
    Service center address in the given city.
  """
  if "new york" in city.lower():
    return {
      "addresses": [
        {
          "name": "Brooklyn dealership",
          "address": "1 2nd Ave, Brooklyn, NY 34567"
        }
      ],
      "status": "SUCCESS"
    }
  else:
    return {
      "status": "NOT_FOUND"
    }