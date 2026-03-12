import datetime
from typing import Any, List, Dict

def get_service_center_info(location: str | None = None, service_type: str | None = None) -> Dict[str, Any]:
    """
    Retrieves information about Cymbal Cars service centers based on location and/or type of service.

    Args:
        location (str | None): The city, state, or zip code to search for service centers. Optional.
        service_type (str | None): The type of service offered (e.g., "Maintenance", "Repairs", "Tire Rotation"). Optional.

    Returns:
        Dict[str, Any]: A dictionary containing the status of the request and a list of service centers
                        with their details (name, address, phone, hours, services), or an error message.
              Example success: {"status": "success", "service_centers": [{"name": "...", "address": "...", ...}]}
              Example no results: {"status": "no_results", "message": "No service centers found for the specified criteria."}
              Example error: {"status": "error", "message": "Invalid input provided."}
    """
    # MOCK: This is a mock implementation. In a real scenario, this would query a database
    # or an external API for service center information.
    # The current_date is not directly used by this tool, but demonstrates how to access context.
    current_date = context.state.get("current_date", datetime.date.today().isoformat())

    mock_service_centers = [
        {
            "name": "Cymbal Cars Service - Downtown LA",
            "address": "123 Main St, Los Angeles, CA 90012",
            "phone": "(213) 555-0100",
            "hours": "Mon-Fri: 8 AM - 6 PM, Sat: 9 AM - 3 PM",
            "services": ["Maintenance", "Repairs", "Diagnostics", "Oil Change"]
        },
        {
            "name": "Cymbal Cars Service - Santa Monica",
            "address": "456 Ocean Ave, Santa Monica, CA 90401",
            "phone": "(310) 555-0200",
            "hours": "Mon-Fri: 8:30 AM - 5:30 PM",
            "services": ["Maintenance", "Tire Services", "Wheel Alignment"]
        },
        {
            "name": "Cymbal Cars Service - Manhattan",
            "address": "789 Broadway, New York, NY 10003",
            "phone": "(212) 555-0300",
            "hours": "Mon-Fri: 7 AM - 7 PM",
            "services": ["Maintenance", "Tire Services", "Brake Repair", "Battery Check"]
        },
        {
            "name": "Cymbal Cars Service - Brooklyn",
            "address": "101 Flatbush Ave, Brooklyn, NY 11217",
            "phone": "(718) 555-0400",
            "hours": "Mon-Fri: 9 AM - 5 PM",
            "services": ["Repairs", "Diagnostics", "Oil Change"]
        },
        {
            "name": "Cymbal Cars Service - Chicago North",
            "address": "321 Lake Shore Dr, Chicago, IL 60611",
            "phone": "(312) 555-0500",
            "hours": "Mon-Sat: 8 AM - 6 PM",
            "services": ["Maintenance", "Repairs", "Tire Services"]
        }
    ]

    filtered_centers = []

    # Fuzzy matching for location
    if location:
        loc_lower = location.lower()
        for center in mock_service_centers:
            address_lower = center["address"].lower()
            if loc_lower in address_lower or \
               (loc_lower == "la" and "los angeles" in address_lower) or \
               (loc_lower == "ny" and ("new york" in address_lower or "brooklyn" in address_lower or "manhattan" in address_lower)) or \
               (loc_lower == "chi" and "chicago" in address_lower):
                filtered_centers.append(center)
        if not filtered_centers:
            return {"status": "no_results", "message": f"No Cymbal Cars service centers found for the specified location: {location}."}
    else:
        filtered_centers = list(mock_service_centers) # If no location, consider all

    # Filter by service type
    if service_type:
        service_type_lower = service_type.lower()
        temp_filtered_centers = []
        for center in filtered_centers:
            if any(service_type_lower in s.lower() for s in center["services"]):
                temp_filtered_centers.append(center)
        filtered_centers = temp_filtered_centers
        if not filtered_centers:
            return {"status": "no_results", "message": f"No Cymbal Cars service centers found offering '{service_type}' in the specified area."}

    if not filtered_centers:
        return {"status": "no_results", "message": "No Cymbal Cars service centers found matching your criteria."}
    else:
        return {"status": "success", "service_centers": filtered_centers}