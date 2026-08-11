from .models import FlightPermit


def flight_permits_with_actors():
    return FlightPermit.objects.select_related("created_by", "updated_by")
